#!/usr/bin/env python
from duckietown_challenges import wrap_solution, ChallengeSolution, ChallengeInterfaceSolution
from myalgorithm import *

class Solver(ChallengeSolution):
    def run(self, cis):
        assert isinstance(cis, ChallengeInterfaceSolution)
        '''
	add the solution code here.
	'''

	#get img_from_eval from evaluator 
	test_set_from_eval_dic = cis.get_challenge_parameters()
	test_set_from_eval = test_set_from_eval_dic['test_set']
	#list of np arrays of shape: (1024, 2048, 3)


	myclass = MyClass() #init class and load weights

	predicted_label_set = list()

	for image in test_set_from_eval:

		label = myclass.run_my_code(image)
		predicted_label_set.append(label)

	data = {'data': predicted_label_set}
	cis.set_solution_output_dict(data)


if __name__ == '__main__':
    wrap_solution(Solver())
