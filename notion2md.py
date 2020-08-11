import os
from pathlib import Path
from urllib.parse import unquote
import shutil
import zipfile
from glob import glob
import re
import csv

# https://github.com/lzakharov/csv2md
class Table:
	def __init__(self, cells):
		self.cells = cells
		self.widths = list(map(max, zip(*[list(map(len, row)) for row in cells])))

	def markdown(self, center_aligned_columns=None, right_aligned_columns=None):
		def format_row(row):
			return '| ' + ' | '.join(row) + ' |'

		rows = [format_row([cell.ljust(width) for cell, width in zip(row, self.widths)]) for row in self.cells]
		separators = ['-' * width for width in self.widths]

		if right_aligned_columns is not None:
			for column in right_aligned_columns:
				separators[column] = ('-' * (self.widths[column] - 1)) + ':'
		if center_aligned_columns is not None:
			for column in center_aligned_columns:
				separators[column] = ':' + ('-' * (self.widths[column] - 2)) + ':'

		rows.insert(1, format_row(separators))

		return '\n'.join(rows)

	@staticmethod
	def parse_csv(file, delimiter=',', quotechar='"'):
		return Table(list(csv.reader(file, delimiter=delimiter, quotechar=quotechar)))


# https://github.com/dreamgonfly/TIL
def main():
	try:
		os.mkdir('./CONVERTED')
	except:
		shutil.rmtree('./CONVERTED')
		os.mkdir('./CONVERTED')

	EXPORT_ZIP_DIR = Path('./')
	MD_REPO = Path('./CONVERTED')

	args_zip = [x for x in os.listdir(EXPORT_ZIP_DIR)
					if x.startswith('Export-') and x.endswith('.zip')]

	for zip_filename in args_zip:
		# zip 경로, 압축풀곳
		path_to_zip_file = Path(EXPORT_ZIP_DIR, zip_filename)
		directory_to_extract_to = Path(EXPORT_ZIP_DIR, path_to_zip_file.stem)

		# unzip
		with zipfile.ZipFile(path_to_zip_file, 'r') as zf:
			zipInfo = zf.infolist()
			for member in zipInfo:
				try:
					# print(member.filename.encode('cp437').decode('euc-kr', 'ignore'))
					# member.filename = member.filename.encode('cp437').decode('euc-kr', 'ignore')
					zf.extract(member, directory_to_extract_to)
				except:
					print('Failed : ', member)
			# zip_ref.extractall(directory_to_extract_to)

		print('-------------------------------------------------')

		for (root,dirs,files) in os.walk(directory_to_extract_to):
			for f in files:
				if not os.path.exists(Path(root,f)):
					continue
				if not re.match('^(\d\d\d\d-\d\d-\d\d-).+(.md)', f):
					continue

				print(f)

				markdown_to_edit = Path(root, f)
				subject_name = ' '.join(markdown_to_edit.stem.split()[:-1])

				assets_folder = Path(root, markdown_to_edit.stem)
				if os.path.exists(assets_folder):
					args_csv = {x[-36:-4]: x for x in os.listdir(assets_folder)
							if x.endswith('.csv')}


				# 파일 제목에 확장자 붙여서
				new_name = subject_name + '.md'
				# 내 git 폴더에 복사
				new_markdown = Path(MD_REPO, new_name)

				# 이미지 옮기기 (원래 md파일 이름과 같은 폴더안에 있음)
				with markdown_to_edit.open(encoding='UTF8') as to_edit, new_markdown.open('w', encoding='UTF8') as editted:
					img_num = 0
					# markdown 파일 라인별로 읽어서
					for line in to_edit:
						# 이미지 경로 찾음
						match = re.match('\!?\[.+?\]\((.+?)\)', line)
						if match:
							# img
							if line[0] == '!':
								path_image = unquote(match.group(1))
								image_name_noext = Path(path_image).stem
								image_name = Path(path_image).name

								image_path = Path(root, path_image)

								new_image_path = Path(MD_REPO, subject_name, image_name)
								new_image_path.parent.mkdir(parents=True, exist_ok=True)
								
								shutil.move(image_path, new_image_path)
								
								new_line = f"![image{img_num}_{image_name_noext}](/assets/img/{subject_name}/{image_name})"
								img_num += 1
								editted.write(new_line)
							# csv
							elif line[-6:-1] == '.csv)':
								with Path(assets_folder, args_csv[line[-38:-6]]).open('r', encoding='utf-8') as csv:
									table = Table.parse_csv(csv, ',', '"')
									editted.write(table.markdown())
									editted.write('\n')
							else:
								editted.write(line)
						else:
							editted.write(line)
				print('DONE', markdown_to_edit)			
		shutil.rmtree(path_to_zip_file.stem)
		

if __name__ == '__main__':
	main()