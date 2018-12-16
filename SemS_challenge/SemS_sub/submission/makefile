evaluate:
	dts challenges evaluate
setup:
	cp -r ../src/lib .

run_regression:
	make setup
	dts challenges submit
	rm -r lib

run_regression_local:
	make setup
	DTSERVER=http://localhost:6544 dts challenges submit
	rm -r lib
