import random
from math import e
import csv

class NeuralNetwork():
    "deep (multi layer) neural network"

    def __init__(self, layers):
        self.__neurons = [0 for x in xrange(len(layers))]
        for i in xrange(len(self.__neurons)):
            self.__neurons[i] = [[0 for x in xrange(2)] for y in xrange(layers[i])]

        self.weights = [0 for x in xrange(len(layers) - 1)]
        for i in xrange(len(self.weights)):
            self.weights[i] = [[0 for x in xrange(layers[i + 1])] for y in xrange(layers[i])]

        self.__der_total_error_to_out_dst_arr = [0 for x in xrange(len(layers)-1)]
        for i in xrange(len(self.weights)):
            self.__der_total_error_to_out_dst_arr[i] = [[0 for x in xrange(layers[i+1])] for y in xrange(layers[i])]

        self.__learning_rate = 0.9

        self.__biases = [0 for x in xrange(len(layers)-1)]

        self.__randomize_weights()

    def __randomize_weights(self):
        for beginLayer in xrange(len(self.weights)):
            for neuronIndex in xrange(len(self.weights[beginLayer])):
                for neuronDst in xrange(len(self.weights[beginLayer][neuronIndex])):
                    self.weights[beginLayer][neuronIndex][neuronDst] = random.random() * 2 - 1

    def get_outpus(self):
        outputs = [0 for x in xrange(len(self.__neurons[-1]))]
        for i in xrange(len(outputs)):
            outputs[i] = self.__neurons[-1][i][1]
        return outputs

    def train_shuffle(self, inputs, targets, epochs):
        """
        trains the neural network - shuffles inputs & targets in eah epoch
        :param inputs: array of inputs to be trained with
        :param targets: array of targets to be trained to
        :param epochs: number of training cycles
        :return:
        """
        if(len(inputs) != len(targets)):
            raise BaseException("train data doesn't match")

        for i in xrange(epochs):
            print "EPOCH:", i
            self.__shuffle_inputs_and_targets(inputs, targets)
            for j in xrange(len(inputs)):
                self.set_inputs(inputs[j])
                self.forward_propagation()
                self.set_targets(targets[j])
                self.back_propagation()

    @staticmethod
    def __shuffle_inputs_and_targets(inputs, targets):
        for i in xrange(len(inputs)/2):
            i_shuffle = random.randint(0,len(inputs)-1)
            j_shuffle = random.randint(0,len(inputs)-1)

            # swap inputs
            temp = [x for x in inputs[i_shuffle]]
            inputs[i_shuffle] = inputs[j_shuffle]
            inputs[j_shuffle] = temp

            #swap targets
            # swap inputs
            temp = [x for x in targets[i_shuffle]]
            targets[i_shuffle] = targets[j_shuffle]
            targets[j_shuffle] = temp

    def set_inputs(self, inputs):
        if len(inputs) != len(self.__neurons[0]):
            raise BaseException("inputs length did not match network inputs length" + str(len(inputs)) + ", " + str(len(self.__neurons[0])))

        for i in xrange(len(self.__neurons[0])):
            self.__neurons[0][i][1] = inputs[i]

    def set_targets(self, targets):
        if len(targets) != len(self.__neurons[0]):
            raise BaseException("targets length did not match network inputs length")

        self.__targets = [x for x in targets]

    def forward_propagation(self):
        for net_layer in xrange(1,len(self.__neurons)):
            for neuron_index_in_net_layer in xrange(len(self.__neurons[net_layer])):
                sum = 0.0
                for neuron_index_in_prev_layer in xrange(len(self.__neurons[net_layer-1])):
                    sum += self.__neurons[net_layer-1][neuron_index_in_prev_layer][1] * self.weights[net_layer - 1][neuron_index_in_prev_layer][neuron_index_in_net_layer]
                sum += self.__biases[net_layer-1]
                self.__neurons[net_layer][neuron_index_in_net_layer][0] = sum
                self.__neurons[net_layer][neuron_index_in_net_layer][1] = self.__calc_sigmoid(sum)


    @staticmethod
    def __calc_sigmoid(x):
        return 1.0 / (1.0 + e**(-x))


    def back_propagation(self):
        copy_weights = self.__copy_3d_arr(self.weights)
        for ii in xrange(len(copy_weights)): #reverse iteration through list
            i = len(copy_weights) - ii - 1
            for j in xrange(len(copy_weights[i])):
                for k in xrange(len(copy_weights[i][j])):
                    self.weights[i][j][k] = self.__adjust_weights(copy_weights, i, j, k)

    def __adjust_weights(self, copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex):
        return copy_weights[layerSrc][neuronSrcIndex][neuronDstIndex] - (self.__der_total_error_to_weight(copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex) * self.__learning_rate)

    def __der_total_error_to_weight(self, copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex):
        return self.der_total_error_to_out_dst(copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex) * self.der_out_dst_to_out_net(copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex) * self.der_out_net_to_weight(copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex)

    def der_total_error_to_out_dst(self, copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex):
        if layerSrc == len(self.__neurons) - 2: # if srcis in the last layer
            self.__der_total_error_to_out_dst_arr[layerSrc][neuronSrcIndex][neuronDstIndex] = self.__neurons[layerSrc+1][neuronDstIndex][1] - self.__targets[neuronDstIndex]
            return self.__der_total_error_to_out_dst_arr[layerSrc][neuronSrcIndex][neuronDstIndex]

        sum = 0.0
        for i in xrange(len(self.__neurons[layerSrc+2])):
            der_total_error_to_net_of_dest = self.__der_total_error_to_out_dst_arr[layerSrc+1][neuronDstIndex][i] * self.der_out_dst_to_out_net(copy_weights, layerSrc+1, neuronDstIndex, i)
            sum += copy_weights[layerSrc+1][neuronDstIndex][i] * der_total_error_to_net_of_dest

        self.__der_total_error_to_out_dst_arr[layerSrc][neuronSrcIndex][neuronDstIndex] = sum
        return self.__der_total_error_to_out_dst_arr[layerSrc][neuronSrcIndex][neuronDstIndex]

    def der_out_dst_to_out_net(self, copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex):
        return self.__neurons[layerSrc+1][neuronDstIndex][1] * (1.0 - self.__neurons[layerSrc+1][neuronDstIndex][1])

    def der_out_net_to_weight(self, copy_weights, layerSrc, neuronSrcIndex, neuronDstIndex):
        return self.__neurons[layerSrc][neuronSrcIndex][1]

    def load_from(self, path):

        with open(path, 'r') as f:
            reader = csv.reader(f)
            index = 0
            for row in reader:
                for beginLayer in xrange(len(self.weights)):
                    for neuronIndex in xrange(len(self.weights[beginLayer])):
                        for neuronDst in xrange(len(self.weights[beginLayer][neuronIndex])):
                            self.weights[beginLayer][neuronIndex][neuronDst] = float(row[index])
                            index += 1


    @staticmethod
    def __copy_3d_arr(weights):
        copy = [0 for x in xrange(len(weights))]
        for i in xrange(len(weights)):
            copy[i] = [0 for y in xrange(len(weights[i]))]
            for j in xrange(len(weights[i])):
                copy[i][j] = [z for z in weights[i][j]]

        return copy

# nn = NeuralNetwork([1,1,1])
# nn.set_inputs([0.4])
# nn.weights[0][0][0] = 0.2
# nn.weights[1][0][0] = 0.3
# nn.forward_propagation()
# print nn.get_outpus()
# nn.set_targets([0.8])
# nn.back_propagation()
# print nn.weights[0][0][0]


# # test NN with SIN func
# from math import sin
# from math import radians
# nn = NeuralNetwork([1,20,5,1])
# INPUT_SIZE = 1000
# EPOCHS = 100
#
# inputs = [[0 for x in xrange(1)] for y in xrange(INPUT_SIZE)]
# targets = [[0 for z in xrange(1)] for w in xrange(INPUT_SIZE)]
#
# for i in xrange(INPUT_SIZE):
#     randAngle = random.random() * 180.0
#     inputs[i] = [randAngle / 180.0]
#     targets[i] = [sin(radians(randAngle))]
#
# print "Begin"
# nn.train_shuffle(inputs, targets, EPOCHS)
# print "Finished"
#
# while 1:
#     angle = input()
#     nn.set_inputs([angle / 180.0])
#     nn.forward_propagation()
#     print nn.get_outpus()