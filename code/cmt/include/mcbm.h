#include "Eigen/Core"
using Eigen::Dynamic;
using Eigen::Array;
using Eigen::VectorXd;
using Eigen::MatrixXd;
using Eigen::ArrayXXd;

#include "conditionaldistribution.h"
#include "exception.h"
#include "lbfgs.h"

class MCBM : public ConditionalDistribution {
	public:
		struct Parameters : public ConditionalDistribution::Parameters {
			public:
				enum Regularizer { L1, L2 };

				bool trainPriors;
				bool trainWeights;
				bool trainFeatures;
				bool trainPredictors;
				bool trainInputBias;
				bool trainOutputBias;
				double regularizeFeatures;
				double regularizePredictors;
				double regularizeWeights;
				Regularizer regularizer;

				Parameters();
				Parameters(const Parameters& params);
				virtual ~Parameters();
				virtual Parameters& operator=(const Parameters& params);
		};

		MCBM(
			int dimIn, 
			int numComponents = 8,
			int numFeatures = -1);
		MCBM(int dimIn, const MCBM& mcbm);

		virtual ~MCBM();

		inline int dimIn() const;
		inline int dimOut() const;

		inline int numComponents() const;
		inline int numFeatures() const;
		inline int numParameters(const Parameters& params = Parameters()) const;

		inline VectorXd priors() const;
		inline void setPriors(const VectorXd& priors);

		inline MatrixXd weights() const;
		inline void setWeights(const MatrixXd& weights);

		inline MatrixXd features() const;
		inline void setFeatures(const MatrixXd& features);

		inline MatrixXd predictors() const;
		inline void setPredictors(const MatrixXd& predictors);

		inline MatrixXd inputBias() const;
		inline void setInputBias(const MatrixXd& inputBias);

		inline VectorXd outputBias() const;
		inline void setOutputBias(const VectorXd& outputBias);

		virtual MatrixXd sample(const MatrixXd& input) const;
		virtual Array<double, 1, Dynamic> logLikelihood(
			const MatrixXd& input,
			const MatrixXd& output) const;

		virtual bool train(
			const MatrixXd& input,
			const MatrixXd& output,
			const Parameters& params = Parameters());
		virtual bool train(
			const MatrixXd& input,
			const MatrixXd& output,
			const MatrixXd& inputVal,
			const MatrixXd& outputVal,
			const Parameters& params = Parameters());
		virtual bool train(
			const MatrixXd& input,
			const MatrixXd& output,
			const MatrixXd* inputVal,
			const MatrixXd* outputVal,
			const Parameters& params = Parameters());

		lbfgsfloatval_t* parameters(const Parameters& params) const;
		void setParameters(const lbfgsfloatval_t* x, const Parameters& params);
		double computeGradient(
			const MatrixXd& input,
			const MatrixXd& output,
			const lbfgsfloatval_t* x,
			lbfgsfloatval_t* g,
			const Parameters& params) const;
		virtual double checkGradient(
			const MatrixXd& input,
			const MatrixXd& output,
			double epsilon = 1e-5,
			const Parameters& params = Parameters()) const;

		virtual pair<pair<ArrayXXd, ArrayXXd>, Array<double, 1, Dynamic> > computeDataGradient(
			const MatrixXd& input,
			const MatrixXd& output) const;

	protected:
		int mDimIn;
		int mNumComponents;
		int mNumFeatures;

		VectorXd mPriors;
		MatrixXd mWeights;
		MatrixXd mFeatures;
		MatrixXd mPredictors;
		MatrixXd mInputBias;
		VectorXd mOutputBias;
};



inline int MCBM::dimIn() const {
	return mDimIn;
}



inline int MCBM::dimOut() const {
	return 1;
}



inline int MCBM::numComponents() const {
	return mNumComponents;
}



inline int MCBM::numFeatures() const {
	return mNumFeatures;
}



inline int MCBM::numParameters(const Parameters& params) const {
	int numParams = 0;
	if(params.trainPriors)
		numParams += mPriors.size();
	if(params.trainWeights)
		numParams += mWeights.size();
	if(params.trainFeatures)
		numParams += mFeatures.size();
	if(params.trainPredictors)
		numParams += mPredictors.size();
	if(params.trainInputBias)
		numParams += mInputBias.size();
	if(params.trainOutputBias)
		numParams += mOutputBias.size();
	return numParams;
}



inline MatrixXd MCBM::weights() const {
	return mWeights;
}



inline void MCBM::setWeights(const MatrixXd& weights) {
	if(weights.rows() != mNumComponents || weights.cols() != mNumFeatures)
		throw Exception("Wrong number of weights.");
	mWeights = weights;
}



inline VectorXd MCBM::priors() const {
	return mPriors;
}



inline void MCBM::setPriors(const VectorXd& priors) {
	if(priors.size() != mNumComponents)
		throw Exception("Wrong number of prior weights.");
	mPriors = priors;
}



inline MatrixXd MCBM::features() const {
	return mFeatures;
}



inline void MCBM::setFeatures(const MatrixXd& features) {
	if(features.rows() != mDimIn)
		throw Exception("Features have wrong dimensionality.");
	if(features.cols() != mNumFeatures)
		throw Exception("Wrong number of features.");
	mFeatures = features;
}



inline MatrixXd MCBM::predictors() const {
	return mPredictors;
}



inline void MCBM::setPredictors(const MatrixXd& predictors) {
	if(predictors.cols() != mDimIn)
		throw Exception("Predictors have wrong dimensionality.");
	if(predictors.rows() != mNumComponents)
		throw Exception("Wrong number of predictors.");
	mPredictors = predictors;
}



inline MatrixXd MCBM::inputBias() const {
	return mInputBias;
}



inline void MCBM::setInputBias(const MatrixXd& inputBias) {
	if(inputBias.rows() != mDimIn)
		throw Exception("Bias vectors have wrong dimensionality.");
	if(inputBias.cols() != mNumComponents)
		throw Exception("Wrong number of bias vectors.");
	mInputBias = inputBias;
}



inline VectorXd MCBM::outputBias() const {
	return mOutputBias;
}



inline void MCBM::setOutputBias(const VectorXd& outputBias) {
	if(outputBias.size() != mNumComponents)
		throw Exception("Wrong number of biases.");
	mOutputBias = outputBias;
}
