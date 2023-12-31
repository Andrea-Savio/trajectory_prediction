#!/usr/bin/env python3

import rospy
import time
from lstm_trainer2 import LSTM_Trainer
import torch
import torch.nn
import numpy as np
from geometry_msgs.msg import Pose
from spencer_tracking_msgs.msg import TrackedPersons
from spencer_tracking_msgs.msg import TrackedPerson
from trajectory_prediction.msg import PredictedTrajectories
from trajectory_prediction.msg import PredictedTrajectory


#msg = None

# Class for saving data of tracked people to use for prediction

class Tracked():
  def __init__(self, id, seq):
    self.id = id
    #self.path = [[0]*3 for i in range(seq)]
    self.path = []
    self.context = []
    self.counter = 0
    self.seq = seq
  
  def get_path(self):
    return self.path
  
  def get_id(self):
    return id

  def get_counter(self, num):
    if self.counter == num:
      return True
    else:
      return False

  def add_detection(self, x, y, z, vx, vy, vz):
    if len(self.path) < self.seq:
      column = [0,0,0]
      column[0] = x
      column[1] = y
      column[2] = z
      #column[3] = np.sqrt(vx**2 + vy**2 + vz**2)
      self.path.append(column)
      self.counter = self.counter + 1
    else:
      self.path.pop(0)
      self.counter = self.counter - 1
      self.add_detection(x, y, z, vx, vy, vz)  

#------------------------------------------------------------------------------------------------------------------------------------

# Subscriber for receiving data of tracked people
"""

class TrackerListener():
  def __init__(self):
    #rospy.init_node('tracker_subscriber')
    self.msg = None
    self.sub = rospy.Subscriber("/spencer/perception/tracked_persons", TrackedPersons, self.tracker_callback)

  def tracker_callback(self, data):
    rospy.loginfo("Returning tracked people data")
    self.msg = data

  def get_data(self):
    return self.msg
"""
#------------------------------------------------------------------------------------------------------------------------------------  

"""
def trajectory_publisher(traj):
  
  rospy.init_node("trajectory_publisher")

  pub = rospy.Publisher("/predicted_trajectories", PredictedTrajectories, queue_size=1000)

  rate = rospy.Rate(7.5)
  while not rospy.is_shutdown():
    pub.publish(traj) 
    rate.sleep()
"""
    
#----------------------------------------------------------------------------------------------------------------------------------

def tracker_callback(msg, args):
    rospy.loginfo("Returning tracked people data")

    msg_list, model, pub, device, seq_length = args
    
    #rospy.loginfo(msg)
    #rospy.loginfo("------------------------------------------------------------------------------------------------------------------")
    
    #msg = data

    for detection in msg.tracks:
      exists = False
      #rospy.loginfo(person)
      #rospy.loginfo("------------------------------------------------------------------------------------------------------------------")
      for person in msg_list:
        rospy.loginfo(len(person.path))

        if detection.track_id == person.id:
          rospy.loginfo("ID matched")
          exists = True
          person.add_detection(detection.pose.pose.position.x, detection.pose.pose.position.y, detection.pose.pose.position.z, detection.twist.twist.linear.x, detection.twist.twist.linear.y, detection.twist.twist.linear.z)
          #print(detection.path)
          rospy.loginfo("Check")

          if len(person.path) == seq_length:
            rospy.loginfo("Time to predict!")
            start = time.time()

            prediction = PredictedTrajectory()

            prediction.track_id = person.id
            prediction.trajectory = [Pose() for k in range(seq_length)]

            #person.path = np.array(person.path)
            #person.path.reshape(1, seq_length, 3)
            rospy.loginfo(person.path)
            #coord = torch.tensor(person.path[seq_length-1], dtype=torch.float32)
            for s in range(int(seq_length/7)):
              coord = torch.tensor(person.path[s:s+7], dtype=torch.float32)
            #rospy.loginfo(coord)
              coord = coord.view(1, 7, 3)
              coord = coord.to(device)
              rospy.loginfo(coord)
              rospy.loginfo("Data ready")
              output = model(coord)[:,-1,:]

              #coord = output
              #del(coord)
              rospy.loginfo(output)
              rospy.loginfo("Output ready")

              prediction.trajectory[s].position.x = output[0,0]
              prediction.trajectory[s].position.y = output[0,1]
              prediction.trajectory[s].position.z = output[0,2]

              prediction.trajectory[s].orientation.x = 0
              prediction.trajectory[s].orientation.y = 0
              prediction.trajectory[s].orientation.z = 0
              prediction.trajectory[s].orientation.w = 0
            
            rospy.loginfo("Prediction ready")
            pub.publish(prediction)
            rospy.loginfo("Prediction published")
            end = time.time()
            print(str(end - start))

            #person.path.pop(0)
            #person.counter = person.counter - 1

            #rospy.loginfo(person.path)
            
            person.path.pop(0)
            person.counter = person.counter - 1

            rospy.loginfo(person.counter)

      if not exists:
          rospy.loginfo("New ID")
          temp = Tracked(detection.track_id, seq_length)
          temp.add_detection(detection.pose.pose.position.x, detection.pose.pose.position.y, detection.pose.pose.position.z, detection.twist.twist.linear.x, detection.twist.twist.linear.y, detection.twist.twist.linear.z)
          temp.counter = temp.counter + 1
          msg_list.append(temp)

# Main

if __name__ == "__main__":

  rospy.init_node("trajectory_publisher")

  pub = rospy.Publisher("/predicted_trajectories", PredictedTrajectory, queue_size=1000)

  device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

  input_dim = 3
  num_layers = 7
  seq_length = 35
  hidden_size = 128
  msg_list = []
  exists = False

  model = LSTM_Trainer(input_dim, num_layers, seq_length, hidden_size)
  model.load_state_dict(torch.load("models/model7_batch_32_final.pt"))
  model.eval()
  model.to(device)



  sub = rospy.Subscriber("/spencer/perception/tracked_persons", TrackedPersons, tracker_callback, (msg_list, model, pub, device, seq_length))

  rospy.spin()


  """
  #tracker = TrackerListener()
  while not rospy.is_shutdown():
    #print(tracker.get_data())
    #msg = tracker.get_data()

    for message in msg_list:
      for detection in message.tracks:
        print("Inside")
        if msg.tracks.track_id == detection.id:
          exists = True
          detection.add_detection(msg.pose.pose.position.x, msg.pose.pose.position.y, msg.pose.pose.position.z)
          #print(detection.path)

          if detection.get_counter(seq_length):
            start = time.time()

            detection.path = np.array(detection.path)
            detection.path.reshape(1, seq_length, 3)

            detection.path = torch.tensor(detection.path, dtype=torch.float32)
            detection.path = detection.path.to(device)

            output = model(detection.path)

            prediction = PredictedTrajectory()

            prediction.track_id = detection.id
            for i in range(seq_length):
              prediction.trajectory[i].position.x = output[1,i,0]
              prediction.trajectory[i].position.y = output[1,i,1]
              prediction.trajectory[i].position.z = output[1,i,2]

              prediction.trajectory[i].pose.x = 0
              prediction.trajectory[i].pose.y = 0
              prediction.trajectory[i].pose.z = 0
              prediction.trajectory[i].pose.w = 0
            
            pub.publish(prediction)

            end = time.time()
            print(str(start - end))

            detection.path.pop(0)
            detection.counter = seq_length - 1

        else:
          print("Inside")
          temp = Tracked(msg.tracks.track_id, seq_length)
          temp.add_detection(msg.pose.pose.position.x, msg.pose.pose.position.y, msg.pose.pose.position.z)
          temp.counter = temp.counter + 1
          msg_list.append(temp)



  #tracked_persons = tracker_subscriber()
"""