package MCTS;

import goTrain.GoLogic;
import MCTS.Policies;

public class GoSimulator{
	public static int simulate(GoLogic originalState, int firstPlayer, Policies.GoNNRolloutPolicy rollOutPolicy){
		GoLogic gameState = originalState.copy();
		int[] move = rollOutPolicy.getMove(gameState);
		boolean passedOnce = false, passedTwice = false, gotStuckOnce = false;
		int movesCounter = 0, passesWhite = 0, passesBlack = 0;
		int tempPlayer = firstPlayer;
		
		int count = 0;
		
		while(!passedTwice){
			count++;
			
			//if(count % 50 == 0){
			if(move != null){
			//	System.out.println(count+":"+move[0]+","+move[1]);
				double[] outputs = rollOutPolicy.nn.getOutputs();
//				System.out.println(outputs[move[0]*9+move[1]]);
//				System.out.println("6,4:" + outputs[6*9+4] + "," + rollOutPolicy.legalMove(gameState, new int[]{6,4}));
//				System.out.println("8,8:" + outputs[8*9+8] + "," + rollOutPolicy.legalMove(gameState, new int[]{8,8}));
////				if(count == 67 || count == 68){
////					System.out.println(gameState.isMoveKoDBG(new int[]{8,8},gameState.turn));
////					gameState.printMe();
////				}
			}
		
			//gameState.printMe();
		//	System.out.println();
			//}
			
			//System.out.println("simulating");
			if(passesWhite >=2 && passesBlack >= 2){
				System.out.println("pass overflow");
				break;
			}
			if(move == null){
				if(tempPlayer == 1)
					passesBlack++;
				else
					passesWhite++;
				gameState.playPassMove();
			}else{
				gameState.makeMove(new Integer(tempPlayer), move);
			}
			movesCounter++;
			tempPlayer = (tempPlayer%2)+1;
			if(movesCounter >= gameState.getSize() * gameState.getSize() * 3){
				if(gotStuckOnce){
					System.out.println("moves overflow twice" + movesCounter);
					//gameState.printMe();
					return gameState.getWin();
				}else{
					System.out.println("moves overflow once" + movesCounter);
					movesCounter = 0;
					move = new Policies.GoRandomRolloutPolicy().getMove(gameState);
					gotStuckOnce = true;
				}
			}else{
				//System.out.println("getting rollout move");
				move = rollOutPolicy.getMove(gameState);
				
				//System.out.println("done getting rollout move");
			}
			
			if(move == null){
				if(passedOnce)
					passedTwice = true;
				else
					passedOnce = true;
			}else
				passedOnce = false;
		}
		//gameState.printMe();
		return gameState.getWin();
		
	}
	
	private static int[] getMove(GoLogic gameState, int playerNum, Policies.GoNNRolloutPolicy player1Policy, Policies.GoNNRolloutPolicy player2Policy){
		if (playerNum == 1)
			return player1Policy.getMove(gameState);
		else
			return player2Policy.getMove(gameState);
	
	}
	
	public static int simulate(GoLogic originalState, int firstPlayer, Policies.GoNNRolloutPolicy player1Policy, Policies.GoNNRolloutPolicy player2Policy){
		return simulate(originalState, firstPlayer, player1Policy, player2Policy, false);
		
	}
	
	public static int simulate(GoLogic originalState, int firstPlayer, Policies.GoNNRolloutPolicy player1Policy, Policies.GoNNRolloutPolicy player2Policy, boolean dbg){
		GoLogic gameState = originalState.copy();
		int[] move = getMove(gameState, firstPlayer, player1Policy, player2Policy);
		boolean passedOnce = false, passedTwice = false, gotStuckOnce = false;
		int movesCounter = 0, passesWhite = 0, passesBlack = 0;
		int tempPlayer = firstPlayer;
		
		int count = 0;
		
		while(!passedTwice){
			count++;
			
			//if(count % 50 == 0){
			if(move != null){
				//System.out.println(count+":"+move[0]+","+move[1]);
				//double[] outputs = rollOutPolicy.nn.getOutputs();
//				System.out.println(outputs[move[0]*9+move[1]]);
//				System.out.println("6,4:" + outputs[6*9+4] + "," + rollOutPolicy.legalMove(gameState, new int[]{6,4}));
//				System.out.println("8,8:" + outputs[8*9+8] + "," + rollOutPolicy.legalMove(gameState, new int[]{8,8}));
////				if(count == 67 || count == 68){
////					System.out.println(gameState.isMoveKoDBG(new int[]{8,8},gameState.turn));
////					gameState.printMe();
////				}
			}
		
			if(dbg && false){
				gameState.printMe();
				System.out.println();
			}
			//}
			
			//System.out.println("simulating");
			if(passesWhite >=2 && passesBlack >= 2){
		//		System.out.println("pass overflow");
				break;
			}
			if(move == null){
				if(tempPlayer == 1)
					passesBlack++;
				else
					passesWhite++;
				gameState.playPassMove();
			}else{
				gameState.makeMove(new Integer(tempPlayer), move);
			}
			movesCounter++;
			tempPlayer = (tempPlayer%2)+1;
			if(movesCounter >= gameState.getSize() * gameState.getSize() * 3){
				if(gotStuckOnce){
					//System.out.println("moves overflow twice" + movesCounter);
				//	gameState.printMe();
					return gameState.getWin();
				}else{
				//	System.out.println("moves overflow once" + movesCounter);
					movesCounter = 0;
					//System.out.println("played random move!***");
					move = new Policies.GoRandomRolloutPolicy().getMove(gameState);
					gotStuckOnce = true;
				}
			}else{
				//System.out.println("getting rollout move");
				move = getMove(gameState, tempPlayer, player1Policy, player2Policy);
				
				//System.out.println("done getting rollout move");
			}
			
			if(move == null){
				if(passedOnce)
					passedTwice = true;
				else
					passedOnce = true;
			}else
				passedOnce = false;
		}
		if(dbg){
			//gameState.printMe();
			//System.out.println();
		}
		//gameState.printMe();
		return gameState.getWin();
		
	}
	
	public static void main(String args[]){
		System.out.println(GoSimulator.simulate(new GoLogic(9), 1,new Policies.GoNNRolloutPolicy("nn_weights.txt")));
	}
	
}
