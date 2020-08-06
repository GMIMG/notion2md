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
		pass
	EXPORT_ZIP_DIR = Path('./')
	MD_REPO = Path('./CONVERTED')

	args_zip = [x for x in os.listdir(EXPORT_ZIP_DIR)
					if x.startswith('Export-') and x.endswith('.zip')]

	for zip_filename in args_zip:
		# zip 경로, 압축풀곳
		path_to_zip_file = Path(EXPORT_ZIP_DIR, zip_filename)
		directory_to_extract_to = Path(EXPORT_ZIP_DIR, path_to_zip_file.stem)

		# unzip
		with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
			zip_ref.extractall(directory_to_extract_to)

		# markdown만 가져오기
		glob_result = list(directory_to_extract_to.glob('*.md'))
		# 가져온게 1개가 아니면 에러(assert)
		assert len(glob_result) == 1
		# 첫번째 파일
		markdown_to_edit = glob_result[0]
		# 을 제목으로 하기
		subject_name = '-'.join(markdown_to_edit.stem.split('-'))

		assets_folder = Path(directory_to_extract_to, markdown_to_edit.stem)
		args_csv = {x[-36:-4]: x for x in os.listdir(assets_folder)
				if x.endswith('.csv')}

		# 파일 제목에 확장자 붙여서
		new_name = subject_name + '.md'
		# 내 git 폴더에 복사
		new_markdown = MD_REPO.joinpath(new_name)

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
						image_name = unquote(match.group(1))
						file_name = os.path.basename(image_name)
						file_name = os.path.splitext(file_name)[0]
						image_path = directory_to_extract_to.joinpath(image_name)
						# github에서는 images 라는 폴더에 넣어서 관리
						# new_image_path = MD_REPO.joinpath('assets/img', image_name)
						new_image_path = MD_REPO.joinpath(image_name)
						new_image_path.parent.mkdir(parents=True, exist_ok=True)
						# image_path.rename(new_image_path)
						shutil.move(image_path, new_image_path)
						# new_line = f"![image{img_num}_{file_name}](assets/img/{image_name})"
						new_line = f"![image{img_num}_{file_name}]({image_name})"
						img_num += 1
						editted.write(new_line)
					# csv
					elif line[-6:-1] == '.csv)':
						with Path(assets_folder, args_csv[line[-38:-6]]).open('r', encoding='utf-8') as csv:
							table = Table.parse_csv(csv, ',', '"')
							editted.write(table.markdown())
					else:
						editted.write(line)
				else:
					editted.write(line)
				
		shutil.rmtree(path_to_zip_file.stem)

if __name__ == '__main__':
	main()