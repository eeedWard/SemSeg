setup: 
	python setup.py develop --prefix ~/.local

clean:
	rm -r out-comptests

tests:
	comptests --nonose lib_tests

evaluate: 
	dts challenges evaluate
generate_submissions:
	python generate_submissions.py config submission_directory
