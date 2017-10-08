package MCTS;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import MCTS.Policies.GoNNExpantionPolicy;
import MCTS.Policies.GoNNRolloutPolicy;
import goTrain.GoLogic;

public class MCTS {

	
	private GoNNExpantionPolicy expansionPolicy;
	private GoNNRolloutPolicy rolloutPolicy;
	private GoSimulator simulator;
	
	public MCTS(GoNNExpantionPolicy expansionPolicy, GoNNRolloutPolicy rolloutPolicy, GoSimulator simulator){
		this.expansionPolicy = expansionPolicy;
		this.rolloutPolicy = rolloutPolicy;
		this.simulator = simulator;
	}
	
	public int[] getMove(GoLogic gameState, int player, int rolloutTimes){
		final int TIMES = rolloutTimes;
		Node root = new Node(player,gameState, new int[0],null,0,0);
		root.setChildrenMoves(this.expansionPolicy.getMoves(root.gameState));
		
		// do MCTS repeatedly 'TIMES'
		for(int i = 0; i < TIMES; i++){
			System.out.println(i);
			this.mcts(root);
		}
		
		double maxScore = -1;
		Node maxChild = null;
		for(Node child : root.children){
			double childScore = child.wins / child.plays;
			if(child.isCaptureOrAtariMove())
				childScore = (childScore+child.move[2]) * 1.5;
			System.out.println(childScore + "," + child.wins + "," + child.plays + Arrays.toString(child.move));
			//note: I changed that in the actual root's move selection (not travel down the tree) will choce that move with the highest win rate (without taking the exploration factor into account)
			if(childScore > maxScore){
				maxScore = childScore;
				maxChild = child;
			}
		}
		return maxChild.move;
	}
	
	public int[] getNextExpansionMove(Node node){
		List<Move> alreadyChildrenOfNode = new ArrayList<Move>();
		for(Node child : node.children){
			alreadyChildrenOfNode.add(new Move(child.move[0], child.move[1]));
		}
		for(int[] move : node.childrenMoves){
			if(!alreadyChildrenOfNode.contains(new Move(move[0],move[1]))){
				return move;
			}
		}
		return new int[0];
	
		
	}
	
	/**
	 * recursive monte carlo tree search for given node
	 * @param node
	 */
	public void mcts(Node node){
		if(node.gameState.gameFinished()){
			node.rollOut(this.simulator, this.rolloutPolicy);
			return;
		}
		int[] possibleMoveWithoutChild = this.getNextExpansionMove(node);
		
		if(possibleMoveWithoutChild.length == 0){
			//selection
			//go to child with max UCT value
			double maxScore = 0;
			Node maxChild = null;
			for(Node child : node.children){
				if(child.UCT() > maxScore){
					maxScore = child.UCT();
					maxChild = child;
				}
			}
			this.mcts(maxChild);
		}else{
			//expansion
			Node newChild = new Node((node.playerNum%2)+1, node.gameState, possibleMoveWithoutChild, node,0,0);
			newChild.setChildrenMoves(this.expansionPolicy.getMoves(newChild.gameState));
			newChild.rollOut(this.simulator, this.rolloutPolicy);
			node.children.add(newChild);
		}
	}
	
	
	private static class Node{
		private static double C = Math.sqrt(2);
		private int playerNum;
		private Node parent;
		private double wins, plays;
		private GoLogic gameState;
		private int[] move;
		private List<Node> children;
		private List<int[]> childrenMoves;
		
		public Node(int _playerNum, GoLogic _gameState, int[] _move, Node _parent, double _wins, double _plays){
			
			this.children = new ArrayList<Node>();
			this.playerNum = _playerNum;
			this.gameState = _gameState.copy();
			if(_move.length != 0)
				this.gameState.makeMove((_playerNum%2)+1, _move);
			if(_move.length == 0)
				this.move = new int[0];
			else{
				if(_move.length == 3)
					this.move = new int[]{_move[0],_move[1], _move[2]};
				else
					this.move = new int[]{_move[0],_move[1]};
			}
			this.parent = _parent;
			this.wins = _wins;
			this.plays = _plays;
			
		}

		/**
		 * returns the UCT score of this node for the selection stage
		 * @return
		 */
		public double UCT(){
			return (this.wins/this.plays) + (C * Math.sqrt((Math.log(this.parent.plays)/Math.log(Math.E))/this.plays));
		}
		
		public void rollOut(GoSimulator simulator, GoNNRolloutPolicy rolloutPolicy){
			int win = simulator.simulate(this.gameState, this.playerNum, rolloutPolicy);
			Node temp = this;
			while(temp != null){
				temp.plays++;
				if(win != 0 && (temp.playerNum%2)+1 == win){
					temp.wins++;
				}
				if(win == 3)
					temp.wins += 0.5;
				
				temp = temp.parent;
			}
			
		}
		
		public void setChildrenMoves(List<int[]> moves){
			this.childrenMoves = moves;
		}
		
		public boolean isCaptureOrAtariMove(){
			return this.move.length == 3;
		}
		
	}
	
	public static class Move{
		public int row;
		public int col;
		public Move(int row, int col){
			this.row = row;
			this.col = col;
		}
		
		@Override
		public boolean equals(Object other){
			if(!(other instanceof Move))
				return false;
			Move otherMove = (Move) other;
			return row == otherMove.row && col == otherMove.col;
		}
		
		@Override
		public int hashCode(){
			int result = row;
		    result = 31 * result + col;
		    return result;
		}
		
		public String toString(){
			return (row + "," + col);
		}
		
	}
	
	
	
}

