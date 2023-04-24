import numpy as np
import matplotlib.pyplot as plt
import gym
import sys
import torch
from torch import nn
from torch import optim

class policy_estimator():
    def __init__(self, env):
        self.n_inputs = env.observation_space.shape[0]
        self.n_outputs = env.action_space.n
        
        # Define network
        self.network = nn.Sequential(
            nn.Linear(self.n_inputs, 16), 
            nn.ReLU(), 
            nn.Linear(16, self.n_outputs),
            nn.Softmax(dim=-1))
    
    def predict(self, state):
        action_probs = self.network(torch.FloatTensor(state))
        return action_probs
    
def discount_rewards(rewards, gamma=0.99):
    r = np.array([gamma**i * rewards[i] 
        for i in range(len(rewards))])
    # Reverse the array direction for cumsum and then
    # revert back to the original order
    r = r[::-1].cumsum()[::-1]
    return r - r.mean()

def reinforce(env, policy_estimator, num_episodes=2000,
              batch_size=25, gamma=0.99):
    # Set up lists to hold results
    total_rewards = []
    batch_rewards = []
    batch_actions = []
    batch_states = []
    batch_counter = 1
    
    # Define optimizer
    optimizer = optim.Adam(policy_estimator.network.parameters(), 
                           lr=LEARNING_RATE)
    
    action_space = np.arange(env.action_space.n)
    ep = 0
    while ep < num_episodes:
        s_0 = env.reset()
        states = []
        rewards = []
        actions = []
        done = False
        while done == False:
            # Get actions and convert to numpy array
            action_probs = policy_estimator.predict(
                s_0).detach().numpy()
            action = np.random.choice(action_space, 
                p=action_probs)
            s_1, r, done, _ = env.step(action)
            
            states.append(s_0)
            rewards.append(r)
            actions.append(action)
            s_0 = s_1
            
            # If done, batch data
            if done:
                batch_rewards.extend(discount_rewards(
                    rewards, gamma))
                batch_states.extend(states)
                batch_actions.extend(actions)
                batch_counter += 1
                total_rewards.append(sum(rewards))
                
                # If batch is complete, update network
                if batch_counter == batch_size:
                    optimizer.zero_grad()
                    state_tensor = torch.FloatTensor(batch_states)
                    reward_tensor = torch.FloatTensor(
                        batch_rewards)
                    # Actions are used as indices, must be 
                    # LongTensor
                    action_tensor = torch.LongTensor(
                       batch_actions)
                    
                    # Calculate loss
                    logprob = torch.log(
                        policy_estimator.predict(state_tensor))
                    
                    #selected_logprobs = reward_tensor * torch.gather(logprob, 1, action_tensor).squeeze()
                    selected_logprobs = reward_tensor * torch.gather(logprob, 1, action_tensor.unsqueeze(1)).squeeze()
                    loss = -selected_logprobs.mean()
                     
                    # Calculate gradients
                    loss.backward()
                    # Apply gradients
                    optimizer.step()
                    
                    batch_rewards = []
                    batch_actions = []
                    batch_states = []
                    batch_counter = 1
                    
                avg_rewards = np.mean(total_rewards[-100:])
                # Print running average
                print("\rEp: {} Average of last 100:" +   
                     "{:.2f}".format(
                     ep + 1, avg_rewards), end="")
                ep += 1
                
    return total_rewards

def smooth_curve_continuous(data, window_size):
    weights = np.repeat(1.0, window_size) / window_size
    smoothed_data = np.convolve(data, weights, mode='valid')
    return smoothed_data

#task = 'CartPole-v1'
task = 'Acrobot-v1'
LEARNING_RATE = .02

env = gym.make(task)


policy_est = policy_estimator(env)
rewards = reinforce(env, policy_est, batch_size=25)
mean_rewards = smooth_curve_continuous(rewards, 20)
plt.figure(figsize=(12,8))
plt.plot(rewards)
plt.plot(mean_rewards)
plt.title("REINFORCE " + task + " lr = " + str(LEARNING_RATE))
plt.xlabel('Episode', fontsize=20)
plt.ylabel('Reward', fontsize=20)
plt.show()
