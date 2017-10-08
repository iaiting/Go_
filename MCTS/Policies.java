package MCTS;


import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;

import MCTS.MCTS.Move;
import goTrain.GoLogic;
import neuralNetImproved.NeuralNetwork;

public class Policies{
	static class Tuple2D<T, S>{
		T first;
		S second;
		public Tuple2D(T t, S s){
			first = t;
			second = s;
		}
	}

	/*
	abstract class ExpansionPolicy{
		int maxExpansionSize;
		
		public ExpansionPolicy(int size){
			maxExpansionSize = size;
		}
		
		abstract boolean legalMove(GoLogic state, int[] move);
		
		abstract List<Tuple2D<int[], Double>> getMovesScore(GoLogic state);
		
		List<int[]> getMoves(GoLogic state){
			List<Tuple2D<int[], Double>> movesByScore = this.getMovesScore(state);
			Collections.sort(movesByScore, new Comparator<Tuple2D<int[], Double>>(){

				@Override
				public int compare(Tuple2D<int[], Double> o1, Tuple2D<int[], Double> o2) {
					if(o1 == o2)
						return 0;
					if(o1.second > o2.second){
						return 1;
					}
					if(o1.second < o2.second){
						return -1;
					}
					return 0;	
				}
				
			});
			Collections.reverse(movesByScore);
			List<int[]> moves = new ArrayList<int[]>();
			int index = 0;
			for(Tuple2D<int[], Double> x : movesByScore){
				if(index >= this.maxExpansionSize)
					break;
				if(this.legalMove(state, x.first)){
					moves.add(x.first);
					index++;
				}
			}
			return moves;
		}
		
	}*/

	static abstract class NNMovesScorer{
		NeuralNetwork nn;
		public NNMovesScorer(String NNWeightsPath){
			nn = new NeuralNetwork(new int[]{9*9*3, 80, 50, 80, 9*9});
			nn.loadFrom(NNWeightsPath);
		}
		
		public NNMovesScorer(NeuralNetwork _nn){
			this.nn = _nn;
		}
		
		public List<Tuple2D<int[], Double>> getMovesScore(GoLogic state){
			//System.out.println("setting inputs");
			nn.setInputs(state.toNNInputArr());
			//System.out.println("done setting inputs");
			nn.forwardPropagation();
			double[] nnOutputs = nn.getOutputs();
			
			List<Tuple2D<int[], Double>> list = new ArrayList<Tuple2D<int[], Double>>();
			for(int i = 0; i < state.getSize()*state.getSize(); i++){
				list.add(new Tuple2D<int[],Double>(new int[]{i/state.getSize(),i%state.getSize()},nnOutputs[i]));
			}
			return list;
		}
		
		public boolean legalMove(GoLogic state, int[] move){
			return state.isLegal(move) && !state.isFillingSelfEye(move);
		}
		
		public List<Tuple2D<int[],Double>> getMovesSortedByScore(GoLogic state){
			List<Tuple2D<int[], Double>> movesByScore = this.getMovesScore(state);
			Collections.sort(movesByScore, new Comparator<Tuple2D<int[], Double>>(){

				@Override
				public int compare(Tuple2D<int[], Double> o1, Tuple2D<int[], Double> o2) {
					if(o1 == o2)
						return 0;
					if(o1.second > o2.second){
						return 1;
					}
					if(o1.second < o2.second){
						return -1;
					}
					return 0;	
				}
				
			});
			Collections.reverse(movesByScore);
			return movesByScore;
		}
	}

	static class GoNNExpantionPolicy extends NNMovesScorer{
		int maxExpansionSize;
		NeuralNetwork nn;
		
		public GoNNExpantionPolicy(int size, String NNWeightsPath){
			super(NNWeightsPath);
			maxExpansionSize = size;
		}
		
			
		List<int[]> getMoves(GoLogic state){
			List<Tuple2D<int[], Double>> movesByScore = super.getMovesSortedByScore(state);
			List<int[]> moves = new ArrayList<int[]>();
			int index = 0;
			for(Tuple2D<int[], Double> x : movesByScore){
				if(index >= this.maxExpansionSize)
					break;
				if(this.legalMove(state, x.first)){
					moves.add(x.first);
					index++;
				}
			}
			return moves;
		}
		
	}
	
	static class GoNNAndCapturesExpansionPolicy extends GoNNExpantionPolicy{

		public GoNNAndCapturesExpansionPolicy(int size, String NNWeightsPath) {
			super(size, NNWeightsPath);
		}
		
		@Override
		List<int[]> getMoves(GoLogic state){
			List<int[]> moves = super.getMoves(state);
			
			//to remove duplications with special moves
			Set<Move> movesSet = new HashSet<Move>();
			for(int[] move : moves){
				movesSet.add(new Move(move[0],move[1]));
			}
			//add all capture moves
			List<int[]> specialMoves = getAllCaptureOrAtariMoves(state);
			for(int[] move : specialMoves){
				if(!movesSet.contains(new Move(move[0],move[1])))
					moves.add(move);
					//movesSet.add(new Move(move[0],move[1]));
			}
			
			
			
			
			//moves.addAll(getAllEscapeAtariMoves(state));
			return moves;
		}
			
		/**
		 * returns all moves that: capture enemy / puts enemy in atari / escape from atari
		 * @param state
		 * @return
		 */
		private List<int[]> getAllCaptureOrAtariMoves(GoLogic state) {
			List<int[]> moves = new ArrayList<int[]>();
			for(int i = 0; i < state.getSize(); i++){
				for(int j = 0; j < state.getSize(); j++){
					//GoLogic copy = state.copy();
					if(state.board[i][j] == 0){
						for(int[] dir : new int[][]{{i+1,j}, {i-1,j}, {i,j+1},{i,j-1}}){
							if(state.validPoint(dir) && state.board[dir[0]][dir[1]] == state.otherPlayer(state.turn)){
								int liberties = state.getLibertiesOfGroup(dir);
								if(liberties == 1 && state.isLegal(new int[]{i,j})){ //captures enemy
									moves.add(new int[]{i,j,3});									
								}else if (liberties == 2 && state.isLegal(new int[]{i,j})){ //puts enemy in atari
									moves.add(new int[]{i,j,1});
								}
							}else if(state.validPoint(dir) && state.board[dir[0]][dir[1]] == state.turn){
								int liberties = state.getLibertiesOfGroup(dir);
								if(liberties == 1 && state.isLegal(new int[]{i,j})){ //escapes from atari
									moves.add(new int[]{i,j,2});
								}
							}
						}
			

//						}
					}
				}
				
			}
			return moves;
		}

	
	}

	public static class GoNNRolloutPolicy extends NNMovesScorer{
		public GoNNRolloutPolicy(String NNWeightsPath){
			super(NNWeightsPath);
		}
		
		public GoNNRolloutPolicy(NeuralNetwork _nn){
			super(_nn);
		}
		
		public int[] getMove(GoLogic state){
			List<Tuple2D<int[], Double>> movesByScore = super.getMovesSortedByScore(state);
			for(Tuple2D<int[],Double> x : movesByScore){
				if(this.legalMove(state, x.first))
					return x.first;
			}
			return null;
		}
	}

	static class GoRandomRolloutPolicy{
		public boolean legalMove(GoLogic state, int[] move){
			return state.isLegal(move) && !state.isFillingSelfEye(move);
		}
		
		
		public int[] getMove(GoLogic state){
			List<int[]> moves = new ArrayList<int[]>();
			for(int i = 0; i < state.getSize(); i++){
				for(int j = 0; j < state.getSize(); j++){
					if(legalMove(state, new int[]{i,j}))
						moves.add(new int[]{i,j});
				}
			}
			if(moves.size() == 0)
				return null;
			Random r = new Random();
			return moves.get(r.nextInt(moves.size()));
		}
		
	}

}

