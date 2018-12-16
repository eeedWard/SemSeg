import os,sys,argparse,shutil
from distutils.dir_util import copy_tree

def create_submissions(config_dir,target_dir):
	if not os.path.exists(target_dir):
			os.makedirs(target_dir)
	for config_file in os.listdir(config_dir):
		f = open(config_dir+'/'+config_file,'r')
		lines = f.read().splitlines()
		target = target_dir+'/'+'submission_'+config_file
		if os.path.exists(target):
			shutil.rmtree(target)
		os.makedirs(target)
		shutil.copytree('src/'+lines[0], target+'/'+lines[0])
		copy_tree('template-submission',target)
		fg = open(target+'/Dockerfile','r')
		r = fg.read().splitlines()
		r[11] = 'COPY /'+lines[0]+'/* /challenge-solution/'
		fg.close()
		fg = open(target+'/Dockerfile','w')
		fg.write('\n'.join(r))
		fg.close()



def main():
	create_submissions(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
	parser=argparse.ArgumentParser(
		description='''Creates submissions for all files in config ''',
		epilog="""Author: Jonas Hongisto""")
	parser.add_argument('String', metavar='Pd', type=str, nargs=1, default='config',
						help='path to config directory')
	parser.add_argument('String', metavar='Px', type=str, nargs=1, default='submission_directory',
						help='path to directory where to put the submissions')
	args=parser.parse_args()

main()