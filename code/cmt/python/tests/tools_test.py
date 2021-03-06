import sys
import unittest

from numpy import *
from numpy import max, all
from numpy.random import *
from cmt.models import MCGSM, GLM, Bernoulli
from cmt.transforms import WhiteningPreconditioner, AffineTransform
from cmt.utils import random_select
from cmt.nonlinear import LogisticFunction
from cmt.tools import generate_data_from_image, sample_image
from cmt.tools import generate_data_from_video, sample_video
from cmt.tools import fill_in_image, fill_in_image_map
from cmt.tools import extract_windows, sample_spike_train
from cmt.tools import generate_masks

class ToolsTest(unittest.TestCase):
	def test_random_select(self):
		# select all elements
		self.assertTrue(set(random_select(8, 8)) == set(range(8)))

		# n should be larger than k
		self.assertRaises(Exception, random_select, 10, 4)



	def test_generate_data_from_image(self):
		xmask = asarray([
			[1, 1],
			[1, 0]], dtype='bool')
		ymask = asarray([
			[0, 0],
			[0, 1]], dtype='bool')

		img = asarray([
			[1., 2.],
			[3., 4.]])

		inputs, outputs = generate_data_from_image(img, xmask, ymask, 1)

		self.assertLess(max(abs(inputs - [[1.], [2.], [3.]])), 1e-10)
		self.assertLess(max(abs(outputs - [[4.]])), 1e-10)

		inputs, outputs = generate_data_from_image(randn(512, 512), xmask, ymask, 100)

		self.assertEqual(inputs.shape[0], 3)
		self.assertEqual(inputs.shape[1], 100)
		self.assertEqual(outputs.shape[0], 1)
		self.assertEqual(outputs.shape[1], 100)

		inputs, outputs = generate_data_from_image(randn(512, 512, 2), xmask, ymask, 100)

		self.assertEqual(inputs.shape[0], 6)
		self.assertEqual(inputs.shape[1], 100)
		self.assertEqual(outputs.shape[0], 2)
		self.assertEqual(outputs.shape[1], 100)

		# multi-channel masks
		xmask = dstack([
			asarray([
				[1, 1],
				[1, 0]], dtype='bool'),
			asarray([
				[1, 1],
				[1, 0]], dtype='bool')])
		ymask = dstack([
			asarray([
				[0, 0],
				[0, 1]], dtype='bool'),
			asarray([
				[0, 0],
				[0, 1]], dtype='bool')])

		inputs, outputs = generate_data_from_image(randn(512, 512, 2), xmask, ymask, 100)

		self.assertEqual(inputs.shape[0], 6)
		self.assertEqual(inputs.shape[1], 100)
		self.assertEqual(outputs.shape[0], 2)
		self.assertEqual(outputs.shape[1], 100)

		# invalid masks due to overlap
		xmask = asarray([
			[1, 1],
			[1, 1]], dtype='bool')
		ymask = asarray([
			[0, 0],
			[0, 1]], dtype='bool')

		self.assertRaises(Exception, generate_data_from_image, img, xmask, ymask, 1)

		# test extracting of 
		xmask = asarray([
			[1, 1],
			[1, 1],
			[1, 0]], dtype='bool')
		ymask = asarray([
			[0, 0],
			[0, 0],
			[0, 1]], dtype='bool')

		# test extracting of all possible inputs and outputs
		img = randn(64, 64)
		inputs, outputs = generate_data_from_image(img, xmask, ymask)

		# try reconstructing image from outputs
		self.assertLess(max(abs(outputs.reshape(62, 63, order='C') - img[2:, 1:])), 1e-16)

		img = randn(64, 64, 3)
		inputs, outputs = generate_data_from_image(img, xmask, ymask)

		img_rec = outputs.reshape(3, 62, 63, order='C')
		img_rec = transpose(img_rec, [1, 2, 0])

		self.assertLess(max(abs(img_rec - img[2:, 1:])), 1e-16)




	def test_generate_data_from_video(self):
		xmask = dstack([
			asarray([
				[1, 1],
				[1, 1]], dtype='bool'),
			asarray([
				[1, 1],
				[1, 0]], dtype='bool')])
		ymask = dstack([
			asarray([
				[0, 0],
				[0, 0]], dtype='bool'),
			asarray([
				[0, 0],
				[0, 1]], dtype='bool')])

		inputs, outputs = generate_data_from_video(randn(512, 512, 5), xmask, ymask, 100)

		self.assertEqual(inputs.shape[0], 7)
		self.assertEqual(inputs.shape[1], 100)
		self.assertEqual(outputs.shape[0], 1)
		self.assertEqual(outputs.shape[1], 100)

		video = randn(38, 63, 10)

		inputs, outputs = generate_data_from_video(video, xmask, ymask)

		video_rec = outputs.reshape(9, 37, 62, order='C').transpose([1, 2, 0])

		self.assertLess(max(abs(video[1:, 1:, 1:] - video_rec)), 1e-16)

		# invalid masks due to overlap
		xmask = dstack([
			asarray([
				[1, 1],
				[1, 1]], dtype='bool'),
			asarray([
				[1, 1],
				[1, 0]], dtype='bool')])
		ymask = dstack([
			asarray([
				[0, 0],
				[0, 1]], dtype='bool'),
			asarray([
				[0, 0],
				[0, 1]], dtype='bool')])

		self.assertRaises(Exception, generate_data_from_video, randn(512, 512, 5), xmask, ymask, 1)



	def test_sample_image(self):
		xmask = asarray([
			[1, 1],
			[1, 0]], dtype='bool')
		ymask = asarray([
			[0, 0],
			[0, 1]], dtype='bool')

		img_init = asarray([
			[1., 2.],
			[3., 4.]])

		model = MCGSM(3, 1)

		img_sample = sample_image(img_init, model, xmask, ymask)

		# only the bottom right-pixel should have been replaced
		self.assertLess(max(abs((img_init - img_sample).ravel()[:3])), 1e-10)

		# test using preconditioner
		wt = WhiteningPreconditioner(randn(3, 1000), randn(1, 1000))
		sample_image(img_init, model, xmask, ymask, wt)

		# test what happens if invalid preconditioner is given
		self.assertRaises(TypeError, sample_image, (img_init, model, xmask, ymask, 10.))
		self.assertRaises(TypeError, sample_image, (img_init, model, xmask, ymask, model))



	def test_sample_video(self):
		xmask = dstack([
			asarray([
				[1, 1, 1],
				[1, 1, 1],
				[1, 1, 1]], dtype='bool'),
			asarray([
				[1, 1, 1],
				[1, 0, 0],
				[0, 0, 0]], dtype='bool')])
		ymask = dstack([
			asarray([
				[0, 0, 0],
				[0, 0, 0],
				[0, 0, 0]], dtype='bool'),
			asarray([
				[0, 0, 0],
				[0, 1, 0],
				[0, 0, 0]], dtype='bool')])

		model = MCGSM(13, 1)

		video_init = randn(64, 64, 5)
		video_sample = sample_video(video_init, model, xmask, ymask)

		# the first frame should be untouched
		self.assertLess(max(abs(video_init[:, :, 0] - video_sample[:, :, 0])), 1e-10)



	def test_fill_in_image(self):
		xmask = asarray([
				[1, 1, 1],
				[1, 0, 0],
				[0, 0, 0]], dtype='bool')
		ymask = asarray([
				[0, 0, 0],
				[0, 1, 0],
				[0, 0, 0]], dtype='bool')
		fmask = rand(10, 10) > .9
		fmask[0] = False
		fmask[:, 0] = False
		fmask[-1] = False
		fmask[:, -1] = False
		img = randn(10, 10)

		model = MCGSM(4, 1)

		# this should raise an exception
		self.assertRaises(TypeError, fill_in_image, (img, model, xmask, ymask, fmask, 10.))

		# this should raise no exception
		wt = WhiteningPreconditioner(randn(4, 1000), randn(1, 1000))
		fill_in_image_map(img, model, xmask, ymask, fmask, wt, num_iter=1, patch_size=20)



	def test_preprocess_spike_train(self):
		stimulus = arange(20).T.reshape(-1, 2).T
		spike_train = arange(10).reshape(1, -1)

		spike_history = 3
		stimulus_history = 2

		stimuli = extract_windows(stimulus, stimulus_history)
		spikes = extract_windows(spike_train, spike_history)

		stimuli = stimuli[:, -spikes.shape[1]:]
		spikes = spikes[:, -stimuli.shape[1]:]

		self.assertEqual(stimuli.shape[0], stimulus.shape[0] * stimulus_history)
		self.assertEqual(stimuli.shape[1], stimulus.shape[1] - max([stimulus_history, spike_history]) + 1)
		self.assertEqual(spikes.shape[0], spike_train.shape[0] * spike_history)
		self.assertEqual(spikes.shape[1], spike_train.shape[1] - max([stimulus_history, spike_history]) + 1)
		self.assertLess(max(abs(spikes[:, -1] - spike_train[0, -spike_history:])), 1e-8)
		self.assertLess(max(abs(stimuli[:, -1] - stimulus[:, -stimulus_history:].T.ravel())), 1e-8)



	def test_sample_spike_train(self):
		inputs = array([
			[0, 0, 0, 0, 1, 1, 1, 1],
			[0, 0, 1, 1, 0, 0, 1, 1],
			[0, 1, 0, 1, 0, 1, 0, 1]])
		outputs = array([[1, 0, 0, 0, 1, 0, 0, 0]])

		glm = GLM(3, LogisticFunction, Bernoulli)
		glm.train(inputs, outputs)

		# generate a spike train without any stimulus input
		spike_train = sample_spike_train(empty([0, 100]), glm, 3)

		# test difference to expected spike train
		diff = spike_train.ravel()[:10] - [0, 0, 0, 1, 0, 0, 1, 0, 0, 1]
		self.assertLess(max(abs(diff)), 1e-8)

		# preconditioner which removes first (uninformative) dimension from input
		m = zeros([3, 1])
		A = array([[0, 1, 0], [0, 0, 1]])
		pre = AffineTransform(m, A)

		glm = GLM(2, LogisticFunction, Bernoulli)
		glm.train(pre(inputs), outputs)

		# generate a spike train with preconditioned spike history
		spike_train = sample_spike_train(empty([0, 100]), glm, 3, pre)

		# test difference to expected spike train
		diff = spike_train.ravel()[:10] - [0, 0, 0, 1, 0, 0, 1, 0, 0, 1]
		self.assertLess(max(abs(diff)), 1e-8)



	def test_generate_maks(self):
		# make sure masks don't overlap
		input_mask, output_mask = generate_masks(7, 1)
		self.assertFalse(any(input_mask & output_mask))

		input_mask, output_mask = generate_masks(8, 2)
		self.assertFalse(any(input_mask & output_mask))

		input_mask, output_mask = generate_masks(7, 1, [1, 0])
		self.assertFalse(any(input_mask & output_mask))

		input_mask, output_mask = generate_masks([3, 7, 7], 3, [1, 0, 0])
		self.assertFalse(any(input_mask & output_mask))



if __name__ == '__main__':
	unittest.main()
