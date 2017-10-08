package neuralNetImproved;


import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Random;
import java.util.Scanner;

import MCTS.GetMove;

/**
 * deep (multi layer) neural network
 * @author Itamar
 *
 */
public class NeuralNetwork{
	
	
	public double[][][] weights; //starting layer, neuron index at starting layer, neuron index at dest layer
	public double[][][] neurons; //inputs=>neurons in input layer, hiddens=>neurons in hidden layer, outputs=>neurons in output layer
	public double learningRate;
	public double targets[];

	public double biases[]; //biases for each layer
	
	public double derTotalErrorToOutDstArr[][][]; //save values to avoid repeated calculations. TODO: a 2D array might be enough
	   
	public NeuralNetwork(int[] layers, double learningRate){
		this.neurons = new double[layers.length][][];
		for(int i = 0; i < neurons.length; i++){
			neurons[i] = new double[layers[i]][2];
		}
		this.weights = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			weights[i] = new double[layers[i]][layers[i+1]];
		}
		
		derTotalErrorToOutDstArr = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			derTotalErrorToOutDstArr[i] = new double[layers[i]][layers[i+1]];
		
		}
		
		this.learningRate = learningRate;
		biases = new double[layers.length-1];
		for(int i = 0; i < biases.length; i++){
			biases[i] = 0;
		}
		
		randomizeWeights();
		
	}
	
	public NeuralNetwork(int[] layers){
		this.neurons = new double[layers.length][][];
		for(int i = 0; i < neurons.length; i++){
			neurons[i] = new double[layers[i]][2];
		}
		this.weights = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			weights[i] = new double[layers[i]][layers[i+1]];
		}
		
		derTotalErrorToOutDstArr = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			derTotalErrorToOutDstArr[i] = new double[layers[i]][layers[i+1]];
		
		}
		
		learningRate = 0.5;
		biases = new double[layers.length-1];
		for(int i = 0; i < biases.length; i++){
			biases[i] = 0;
		}
		
		randomizeWeights();
		
	}
	
	
	public NeuralNetwork(int[][] layers, double[] _biases){
		this.neurons = new double[layers.length][][];
		for(int i = 0; i < neurons.length; i++){
			neurons[i] = new double[layers[i].length][2];
		}
		this.weights = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			weights[i] = new double[layers[i].length][layers[i+1].length];
		}
		
		derTotalErrorToOutDstArr = new double[layers.length-1][][];
		for(int i = 0; i < weights.length; i++){
			derTotalErrorToOutDstArr[i] = new double[layers[i].length][layers[i+1].length];
			
		}
		
		learningRate = 0.9;
		
		this.biases = new double[layers.length-1];
		for(int i = 0; i < this.biases.length; i++){
			this.biases[i] = _biases[i];
		}
		
		randomizeWeights();
	}
	
	
	
	public double[] getOutputs(){
		double[] outputs = new double[neurons[neurons.length-1].length];
		for(int i = 0; i < outputs.length; i++){
			outputs[i] = neurons[neurons.length-1][i][1];
		}
		return outputs;
	}
	
	/**
	 *  NOTICE: for optimal results, should use the method 'trainShuffle'
	 * trains neural network <br>
	 * @param inputs array of inputs to be trained with
	 * @param targets array of targets to be trained to
	 * @param epochs number of training cycles
	 */
	public void train(double[][] inputs, double[][] targets, int epochs){
		if(inputs.length != targets.length){
			System.out.println("train data doesn't match");
			return;
		}
		for(int i = 0; i < epochs; i++){
			System.out.println("EPOCH:" + i);
			//for each epoch iterate over all training data and trian NN for each inputs,target pair
			for(int j = 0; j < inputs.length; j++){
				//System.out.println("data:" + j);
				setInputs(inputs[j]);
				forwardPropagation();
				setTargets(targets[j]);
				backpropagation();
			}
		}
	}
	
	/**
	 * trains neural network - shuffles inputs & targets in each epoch
	 * @param inputs array of inputs to be trained with
	 * @param targets array of targets to be trained to
	 * @param epochs number of training cycles
	 * @param
	 */
	public void trainShuffle(double[][] inputs, double[][] targets, int epochs){
		if(inputs.length != targets.length){
			System.out.println("train data doesn't match");
			return;
		}
		for(int i = 0; i < epochs; i++){
			//System.out.println("EPOCH:" + i);
			shuffleInputsAndTargets(inputs,targets);
			for(int j = 0; j < inputs.length; j++){
				setInputs(inputs[j]);
				forwardPropagation();
				setTargets(targets[j]);
				backpropagation();
			}
		}
	}
	
	private void shuffleInputsAndTargets(double[][] inputs, double[][] targets) {
		Random r = new Random();
		for(int i = 0; i < inputs.length / 2; i++){
			int i_shuffle = r.nextInt(inputs.length);
			int j_shuffle = r.nextInt(inputs.length);
			double[] temp = new double[inputs[i_shuffle].length];
			//swap inputs
			System.arraycopy(inputs[i_shuffle], 0, temp, 0, temp.length );
			//temp = Arrays.copy(inputs[i_shuffle]);
			inputs[i_shuffle] = inputs[j_shuffle];
			inputs[j_shuffle] = temp;
			
			temp = new double[targets[i_shuffle].length];
			//swap targets
			System.arraycopy(targets[i_shuffle], 0, temp, 0, temp.length );
			//temp = Arrays.copy(inputs[i_shuffle]);
			targets[i_shuffle] = targets[j_shuffle];
			targets[j_shuffle] = temp;
		}
		
	}


	public void setInputs(double[] inputs){
		if (inputs.length != this.neurons[0].length){
			System.out.println("inputs length did not match network inputs length");
			return;
		}
		
		for (int i = 0; i < this.neurons[0].length; i++){
			this.neurons[0][i][1] = inputs[i];// there's no meaning to inputs layer net value (only to out value)
		}		
		
	}
	
	public void setTargets (double[] targets){
		if (targets.length != this.neurons[neurons.length-1].length){
			System.out.println("targets length did not match network inputs length");
			return;
		}
		
		this.targets = new double[targets.length];
		
		for (int i = 0; i < targets.length; i++){
			this.targets[i] = targets[i];
		}		
		
	}
	
	/**
	 * propagates network data from inputs to outputs
	 *
	 */
	public void forwardPropagation(){
		//iterate thorugh layers
		for(int netLayer = 1; netLayer < neurons.length; netLayer++){
			
			//iterate through neurons in layer
			for(int neuronIndexInNetLayer = 0; neuronIndexInNetLayer < neurons[netLayer].length; neuronIndexInNetLayer++){
				double sum = 0.0;
				//calculate Sigma(Wi*Xi) - the net of this neuron
				for(int neuronIndexInPrevLayer = 0; neuronIndexInPrevLayer < neurons[netLayer-1].length; neuronIndexInPrevLayer++){
					sum += neurons[netLayer-1][neuronIndexInPrevLayer][1] * weights[netLayer-1][neuronIndexInPrevLayer][neuronIndexInNetLayer];
				}
				sum += biases[netLayer-1];
				//sum += (netLayer == 1) ? biasL1Weight : biasL2Weight;

				//set the sum to the net of the current neuron (neuronIndexInNetLayer)
				//System.out.printf("%d,%d net:%f , ", netLayer, neuronIndexInNetLayer, sum);
				//System.out.printf("%d,%d out:%f \n", netLayer, neuronIndexInNetLayer, calcSigmoid(sum));
				neurons[netLayer][neuronIndexInNetLayer][0] = sum;
				neurons[netLayer][neuronIndexInNetLayer][1] = calcSigmoid(sum);
			}
			
		}
	}
	
	/**
	 * 
	 * @param x value to calc sigmoid func to
	 * @return the sigmoid value for x
	 */
	public static double calcSigmoid(double x) {
		return 1.0 / (1.0 + Math.exp(-x));
	}

	private void randomizeWeights(){
		Random r = new Random();
		for(int beginLayer = 0; beginLayer < weights.length; beginLayer++){
			for(int neuronIndex = 0; neuronIndex < weights[beginLayer].length; neuronIndex++){
				for(int neuronDest = 0; neuronDest < weights[beginLayer][neuronIndex].length; neuronDest++){
					weights[beginLayer][neuronIndex][neuronDest] = Math.random() * 2 - 1 ;
		
				}
			}
		}
	}
	
	public void backpropagation(){
		double[][][] copyWeights = copy3DArr(this.weights);
		for (int i = copyWeights.length - 1; i >= 0; i--) {
			for (int j = 0; j < copyWeights[i].length; j++) {
				for (int k = 0; k < copyWeights[i][j].length; k++) {
				//	System.out.println("back propagation for:" + i+ "," + j);
					weights[i][j][k] = adjustWeights(copyWeights, i, j, k);
					//System.out.println("new weight:" + weights[i][j][k]);
				}
			}
		}
	}
	
	private double adjustWeights(double[][][] copyWeights, int layerSrc, int neuronSrcIndex, int neuronDstIndex) {
		//double tempdbg = derTotalErrorToWeight(copyWeights,layerSrc , neuronSrcIndex, neuronDstIndex);
		//System.out.println("weight gradient:" + tempdbg);
		//System.out.println("***" + layerSrc + "," + neuronSrcIndex + "," + neru);
		return copyWeights[layerSrc][neuronSrcIndex][neuronDstIndex] - (derTotalErrorToWeight(copyWeights,layerSrc , neuronSrcIndex, neuronDstIndex) * learningRate);	
	}

	private double derTotalErrorToWeight(double[][][] copyWeights, int layerSrc, int neuronSrcIndex, int neuronDstIndex) {
		double derTotalErrorToOutDstTemp = derTotalErrorToOutDst(copyWeights, layerSrc, neuronSrcIndex, neuronDstIndex);
		double derOutDstToOutNetTemp = derOutDstToOutNet(copyWeights, layerSrc, neuronSrcIndex, neuronDstIndex);
		double derOutNetToWeightTemp = derOutNetToWeight(copyWeights, layerSrc, neuronSrcIndex, neuronDstIndex);
				
		//derTotalErrorToNetOfDestArr[layerSrc+1][neuronDstIndex] = derTotalErrorToOutDstTemp * derOutDstToOutNetTemp;
		//System.out.printf("%d,%d,%d:%f\n",layerSrc, neuronSrcIndex, neuronDstIndex,derTotalErrorToOutDstTemp * derOutDstToOutNetTemp * derOutNetToWeightTemp );
		return derTotalErrorToOutDstTemp * derOutDstToOutNetTemp * derOutNetToWeightTemp;
	}

	private double derTotalErrorToOutDst(double[][][] copyWeights, int layerSrc, int neuronSrcIndex, int neuronDstIndex) {
		//if src is in the last layer
		if(layerSrc == neurons.length-2){
			//System.out.printf("%d,%d,%d, derTotalErrorToOutDst:%f\n",layerSrc,neuronSrcIndex, neuronDstIndex, neurons[layerSrc+1][neuronDstIndex][1] - targets[neuronDstIndex]);
			derTotalErrorToOutDstArr[layerSrc][ neuronSrcIndex] [neuronDstIndex] = neurons[layerSrc+1][neuronDstIndex][1] - targets[neuronDstIndex];
			
			
			return derTotalErrorToOutDstArr[layerSrc][ neuronSrcIndex] [neuronDstIndex];
		}
		//else src is not in the last layer - things get FUN
		double sum = 0.0;
		//loop through all neurons in dst layer
		for(int i = 0; i < neurons[layerSrc+2].length; i++){
			double derTotalErrorToNetOfDest = derTotalErrorToOutDstArr[layerSrc+1][ neuronDstIndex] [i] * derOutDstToOutNet(copyWeights, layerSrc+1,  neuronDstIndex, i);
			
			sum += copyWeights[layerSrc+1][neuronDstIndex][i] * derTotalErrorToNetOfDest;
		}
		//System.out.printf("%d,%d,%d, derTotalErrorToOutDst:%f\n",layerSrc,neuronSrcIndex, neuronDstIndex, sum);
		derTotalErrorToOutDstArr[layerSrc][ neuronSrcIndex] [neuronDstIndex] =  sum;
		return derTotalErrorToOutDstArr[layerSrc][ neuronSrcIndex] [neuronDstIndex];
	}

	private double derOutDstToOutNet(double[][][] copyWeights, int layerSrc, int neuronSrcIndex, int neuronDstIndex) {
		//derivative of sigmoiod is f(x)*(1-f(x))
		//System.out.printf("%d,%d,%d, derOutDstToOutNet:%f\n",layerSrc,neuronSrcIndex, neuronDstIndex, neurons[layerSrc+1][neuronDstIndex][1] *(1.0 - neurons[layerSrc+1][neuronDstIndex][1]));
		return neurons[layerSrc+1][neuronDstIndex][1] *(1.0 - neurons[layerSrc+1][neuronDstIndex][1]);
	
	}

	private double derOutNetToWeight(double[][][] copyWeights, int layerSrc, int neuronSrcIndex, int neuronDstIndex) {
		//System.out.printf("%d,%d,%d, derOutNetToWeight:%f\n",layerSrc,neuronSrcIndex, neuronDstIndex, this.neurons[layerSrc][neuronSrcIndex][1]);

		return this.neurons[layerSrc][neuronSrcIndex][1];
	}

	public static double[][][] copy3DArr(double[][][] weights) {
		double[][][] copy = new double[weights.length][][];
		for (int i = 0; i < weights.length; i++) {
			copy[i] = new double[weights[i].length][];
			for (int j = 0; j < weights[i].length; j++) {
				copy[i][j] = new double[weights[i][j].length];
				for (int j2 = 0; j2 < weights[i][j].length; j2++) {
					copy[i][j][j2] = weights[i][j][j2];
				}
			}
		}
		return copy;
	}

	
	/**
	 * saves network weights as CSV text file
	 * @param PATH
	 */
	public void saveTo(final String PATH){
	      FileOutputStream out = null;

	      try {
	    
	         out = new FileOutputStream(PATH);
	         
	         for(int beginLayer = 0; beginLayer < weights.length; beginLayer++){
	 			for(int neuronIndex = 0; neuronIndex < weights[beginLayer].length; neuronIndex++){
	 				for(int neuronDest = 0; neuronDest < weights[beginLayer][neuronIndex].length; neuronDest++){
	 					out.write((String.valueOf(weights[beginLayer][neuronIndex][neuronDest]) + ",").getBytes());
	 					
	 		
	 				}
	 			}
	 		}
	         
	      } catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}finally {
	       
	         if (out != null) {
	            try {
					out.close();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
	         }
	      }
	}
	
	/**
	 * loads network weights from CSV text file
	 * @param PATH
	 */
	public void loadFrom(final String PATH){
		Scanner s;
		try {
			if(NeuralNetwork.class.getResourceAsStream(PATH) == null){
				s = new Scanner(new File(PATH));				
			}else{
				s = new Scanner(new InputStreamReader(GetMove.class.getResourceAsStream(PATH)));
			}
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			return;
		}
		s.useDelimiter(",");
		
		      try {
		    
		
		         
		         for(int beginLayer = 0; beginLayer < weights.length; beginLayer++){
		 			for(int neuronIndex = 0; neuronIndex < weights[beginLayer].length; neuronIndex++){
		 				for(int neuronDest = 0; neuronDest < weights[beginLayer][neuronIndex].length; neuronDest++){
		 					String next = s.next();
		 					weights[beginLayer][neuronIndex][neuronDest] = Double.valueOf(next);
		 					//System.out.println(weights[beginLayer][neuronIndex][neuronDest]); 
		 						
		 				}
		 			}
		 		}
		         
		      }finally {
		       
		         if (s != null) {
		            	s.close();
				}
		      }
	}
	
	public String toString(){
		String str = "";
		for(int beginLayer = 0; beginLayer < weights.length; beginLayer++){
			for(int neuronIndex = 0; neuronIndex < weights[beginLayer].length; neuronIndex++){
				for(int neuronDest = 0; neuronDest < weights[beginLayer][neuronIndex].length; neuronDest++){
					str += beginLayer + "," + neuronIndex + "," + "->" + weights[beginLayer][neuronIndex][neuronDest] + ":" + neuronDest + "\n";
				}
			}
		}
		return str;
	}
	
}
