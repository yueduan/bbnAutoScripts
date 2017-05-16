import subprocess, os 
import fcntl 
import time
import binascii
import sys
import shutil

###CONFIG BEGIN###

EMULATOR_PATH = "/home/yduan/yueduan/android-5.0.0_r3/external/droidscope_art/"
SYS_DIR_PATH = "/home/yduan/yueduan/android-5.0.0_r3/out/target/product/generic"
KERNEL_FILE_PATH = "/home/yduan/yueduan/android-5.0.0_r3/android_art_kernel/goldfish/arch/arm/boot/zImage"
SYS_DIR_SRC_PATH = "/androidSysImages/"

PLUGIN_PATH = "/home/yduan/yueduan/android-5.0.0_r3/external/droidscope_art/DECAF_plugins/bbn_resource_usage_analysis/libjavatracer.so"
TEMP_RESULT_PATH = "/home/yduan/yueduan/android-5.0.0_r3/external/droidscope_art/DECAF_plugins/bbn_resource_usage_analysis/out/"
RESULT_PATH = "/results/"
APP_PATH = "/test_apps/"

EXECUTION_TIME = 30

###CONFIG END#####

# Given one directory, delete all its files and subdirectories
def cleanDir(path):
	for root, dirs, files in os.walk(path):
		for f in files:
			os.unlink(os.path.join(root, f))
		for d in dirs:
 			shutil.rmtree(os.path.join(root, d))

# Move all the files from directory 'pathSrc' to directory 'pathDst'
def moveAllFiles(pathSrc, pathDst):
	for root, dirs, files in os.walk(pathSrc):
		for f in files:
			src = os.path.join(pathSrc, f)
			dst = os.path.join(pathDst, f)
			os.rename(src, dst)

def input_cmd(p, cmd): 
	if not cmd.endswith("\n"): 
		cmd += "\n" 
	p.stdin.write(cmd) 
	p.stdin.write("MARK\n") 
	while True: 
		time.sleep(0.1) 
		try: 
			s = p.stdout.read() 
 		except Exception, e:
			continue 
		print s 
		if "unknown command: 'MARK'" in s: 
			break


def wait_start(proc):
	proc.stdin.write("ps\n")
	proc.stdin.write("MARK\n")
	while True:
		time.sleep(5)
		try:    
			s = proc.stdout.read()
		except Exception, e:
			continue
		if "unknown command: 'MARK'" in s:
			if "com.android.managedprovisioning" in s:
				break
			else:
				proc.stdin.write("ps\n")
				proc.stdin.write("MARK\n")
	print "emulator ready"
	time.sleep(10)



def checkProcess(proc, name):
	proc.stdin.write("ps\n")
	time.sleep(1)

	try:
		s = proc.stdout.read()
		input_cmd(proc, "ps")
	except Exception, e:
		return 0
	if name in s:
		print "app launched"
		return 1
	return 0



def main():
	#shutil.copyfile("/bbnAutoScripts/libunpacker.so", PLUGIN_PATH)
	cleanDir(RESULT_PATH)
	try:
		pl = subprocess.Popen(['ps', '-U', '0'], stdout=subprocess.PIPE).communicate()[0]
        	if not 'emulator' in pl:
		
			# move all system image files to the destination folder in order to run multiple docker containers in parallel
			moveAllFiles(SYS_DIR_SRC_PATH, SYS_DIR_PATH)

			# start droidscope   
			os.chdir("/home/yduan/yueduan/android-5.0.0_r3/external/droidscope_art/")
			p = subprocess.Popen(args="sudo ./objs/emulator -sdcard mySdCardFile.img -no-audio -no-window -partition-size 1000 -sysdir /home/yduan/yueduan/android-5.0.0_r3/out/target/product/generic -kernel /home/yduan/yueduan/android-5.0.0_r3/android_art_kernel/goldfish/arch/arm/boot/zImage -memory 2048 -qemu -monitor stdio", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
 			fl = fcntl.fcntl(p.stdout, fcntl.F_GETFL)
 			fcntl.fcntl(p.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
 			time.sleep(5)
	
			# wait for the emulator to fully start
	 		input_cmd(p, "ps")
	 		wait_start(p)
		else:
			print 'kill existing emulator first!'
			return

		# go over every file in APP_PATH, install the app, run it in emulator to analyze and then uninstall the app
	 	for dirname, dirnames, filenames in os.walk(APP_PATH):
			for filename in filenames:
				file_path = os.path.join(dirname, filename)
				print "Installing: " + file_path
				cmd = "/bbnAutoScripts/install_uninstall.sh {} 1".format(file_path)
				proc_install = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    				(output, err) = proc_install.communicate()
				print output
					
				# after installation, load the plugin
				print "Loading plugin"
 				input_cmd(p, "load_plugin {plugin}".format(plugin=PLUGIN_PATH))

				# get package name of the app and hook the process
				packageName = subprocess.check_output(['/bbnAutoScripts/getPackageNameFromApk.sh',file_path])
				cmd = "do_hookapitests {}".format(packageName)
				input_cmd(p, cmd)

				# launch the app
				print "Launching the app"
				cmd = "/bbnAutoScripts/launch_KillApp.sh {} 1".format(file_path)
				proc_launch = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				(output, err) = proc_launch.communicate()
				print output

				
				# let the app execute for certain time if it is successfully launched
				time.sleep(5)
				check_ret = checkProcess(p, packageName)
				if check_ret == 1:				
					time.sleep(EXECUTION_TIME)

				# unload the plugin and uninstall the app
				print "unloading plugin"
				input_cmd(p, "unload_plugin")
		
				# clean up the app
				print "Uninstalling: " + file_path
				cmd = "/bbnAutoScripts/install_uninstall.sh {} 2".format(file_path)
				proc_uninstall = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				(output, err) = proc_uninstall.communicate()
				print output

				# move the result files into a specific folder
				result_path_new = RESULT_PATH + filename
				os.mkdir(result_path_new)
				moveAllFiles(TEMP_RESULT_PATH, result_path_new)
				
				
	except IOError as e:
		print "I/O error({0}): {1}".format(e.errno, e.strerror)
	except:
		print "Unexpected error:", sys.exc_info()[0]
		raise


if __name__ == '__main__':
 	main()
