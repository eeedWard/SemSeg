from comptests import comptest, run_module_tests

#fails
@comptest
def dummy_test_1():
    a = [1,2]
    b = a[0]
    print('Hello1')
#passes
@comptest
def dummy_test_2():
    a = [1,2]
    b = a[1]
    print('Hello2')
