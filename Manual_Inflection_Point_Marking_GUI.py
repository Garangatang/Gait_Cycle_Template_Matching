"""
Description: This GUI can be used to manually mark a subsection of inflection points within underfoot pressure data.
    This subsection of data can be used to construct a template within Gait_Cycle_Template_Matching.py which can 
    find all inflection points within the larger dataset.

Written by Grange Simpson
Version: 2024.12.15

Usage: When you run the file a file selector will be opened. A Python dictionary containing key: dataset name, and
    value: dataset compressed into a pandas .pkl file is the only acceptable file type. Select the appropriate .pkl
    file and it should be loaded into the GUI. 

    Important: with this current file version, self.datalength will need to be adjusted according to the sampling
    rate of the input data so an appropriate subsection of data can have its inflection points marked.

    After inflection points have been marked, saved_inflection_point_dictionary.pkl which contains a dictionary will 
    be output key: dataset name, value: marked inflection points for that dataset input into Gait_Cycle_Template_Matching.py
Recommendations: 
"""

import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QFileDialog
import pyqtgraph as pg
import os
import pandas as pd
import pickle as pkl

class SignalGraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Selection of Inflection Points")
        self.setGeometry(200, 200, 1600, 1200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create the graph
        self.graph_widget = pg.PlotWidget()
        main_layout.addWidget(self.graph_widget)

        self.click_locations = []
        # Markers to show in the graph GUI
        self.markers = []
        self.saved_indices = []
        # Dictionary for saving the inflection point indices with their data
        self.savedInflPointDict = {}

        # Generate sample signal data
        self.normPressDict = {}
        self.x = None
        self.y = None
        self.keyIndex = None
        self.dataKeys = None
        self.dataLength = 1500
        if (self.x == None and self.y == None):
            self.file_path = None
            self.open_file_dialog()
            self.load_pkl_file_data()
            self.update_graph_data_forward()
        
        # Plot the signal
        pen = pg.mkPen(color='r', width=3)
        self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)

        # Enable mouse clicking on the plot
        self.graph_widget.scene().sigMouseClicked.connect(self.on_plot_click)

        # Create buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.clear_button = QPushButton("Clear All Selections")
        self.clear_button.clicked.connect(self.clear_selections)
        button_layout.addWidget(self.clear_button)

        self.save_button = QPushButton("Save Indices")
        self.save_button.clicked.connect(self.save_indices)
        button_layout.addWidget(self.save_button)

        # Switch the data graph back to the previous data seen
        self.update_graph_backward_button = QPushButton("Go Backward to Next Data Section")
        self.update_graph_backward_button.clicked.connect(self.change_data_to_mark_backward)
        button_layout.addWidget(self.update_graph_backward_button)

        # Switch the data graph back to the next data
        self.update_graph_forward_button = QPushButton("Go Forward to Next Data Section")
        self.update_graph_forward_button.clicked.connect(self.change_data_to_mark_forward)
        button_layout.addWidget(self.update_graph_forward_button)  
        

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", options=options)
        if file_name:
            self.file_path = file_name

    # Load data stored in pkl files for manual inflection point marking
    def load_pkl_file_data(self):
        self.dataDirectory = './'
        terrFileList = [f for f in os.listdir(self.dataDirectory) if f.endswith('.pkl')]

        """
        # loading all TIP data
        for terrFile in terrFileList:
            TIP_num = terrFile.split("_")[0]
            terr = terrFile.split("_")[3]
            terr = terr.split(".")[0]
            file_path = os.path.join(self.dataDirectory, terrFile)
            df = pd.read_pickle(file_path)
            self.normPressDict[TIP_num + "_" + terr] = df
        """
        with open(self.file_path, 'rb') as file:
            # Load the dictionary from the file
            self.normPressDict = pkl.load(file)

        self.dataKeys = list(self.normPressDict.keys())

    # Update the graph to new data
    def update_graph_data_forward(self):
        if (self.keyIndex == None):
            self.keyIndex = 0
            # Set up the 
            self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
            self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()

        elif (self.normPressDict != None and self.keyIndex < len(self.dataKeys) - 1):
            
            self.keyIndex += 1
            self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
            self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()

            # Showing previously clicked points if navigating backward.
            """
            if (len(self.savedInflPointDict[self.dataKeys[self.keyIndex]]) > 0):
                self.click_locations = 
                marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=10, symbolBrush='m')
            """
        self.setWindowTitle("Manual Selection of Inflection Points " + str(self.keyIndex + 1) + "/" + str(len(self.dataKeys)))

        

    # Update the graph to previous data
    def update_graph_data_backward(self):
        
        if (self.keyIndex == None):
            self.keyIndex = 0
            
        if (self.normPressDict != None and self.keyIndex != 0):
            self.keyIndex -= 1
            #print(self.dataKeys[self.keyIndex])
            #print(len(self.normPressDict[self.dataKeys[self.keyIndex]]))
            self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
            self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()
        
        self.setWindowTitle("Manual Selection of Inflection Points " + str(self.keyIndex + 1) + "/" + str(len(self.dataKeys)))
        
    # Move to the next dataset to mark.    
    def change_data_to_mark_forward(self):
        self.save_indices()
        self.update_graph_data_forward()
        self.graph_widget.clear()
        pen = pg.mkPen(color='r', width=3)
        self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)
        #self.save_indices()

    # Move to the previous dataset to mark
    def change_data_to_mark_backward(self):
        self.save_indices()
        self.update_graph_data_backward()
        self.graph_widget.clear()
        pen = pg.mkPen(color='r', width=3)
        self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)
        #self.save_indices()

    # Flow for methods when the graph is clicked.
    def on_plot_click(self, event):
        pos = event.scenePos()
        if self.graph_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.graph_widget.plotItem.vb.mapSceneToView(pos)
            clicked_x, clicked_y = mouse_point.x(), mouse_point.y()
            #pos = event.scenePos()
            index = self.find_nearest_point(clicked_x, clicked_y)
            
            if index is not None:
                x, y = self.x[index], self.y[index]
                minLastClickedPointDist = np.abs(self.click_locations - index)
                # Clearing point if click is near another previously selected point
                if (len(minLastClickedPointDist) > 0 and min(minLastClickedPointDist) < 15):
                    minLocation = np.array(minLastClickedPointDist).argmin()
                    #print("Markers")
                    #print(self.markers)
                    del_marker = self.markers[minLocation]
                    self.graph_widget.removeItem(del_marker)
                    del self.click_locations[minLocation]
                    del self.markers[minLocation]
                
                # Adding clicked point to the graph
                else:
                    self.click_locations.append(index)
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=10, symbolBrush='m')
                    self.markers.append(marker)

                print(f"Clicked at index: {index}, x={x:.2f}, y={y:.2f}")       
                print(self.click_locations)  

    # Map the click onto the graph if click is close enough.
    def find_nearest_point(self, clicked_x, clicked_y):
        index = np.argmin(np.abs(self.x - clicked_x))
        y_tolerance = 0.2
        if abs(self.y[index] - clicked_y) <= y_tolerance:
            return index
        return None

    # Clear all selections made on the graph.
    def clear_selections(self):
        for marker in self.markers:
            self.graph_widget.removeItem(marker)
        self.markers.clear()
        self.click_locations.clear()
        print("All selections cleared")

    # Remove the last selection made.
    def remove_last_selection(self):
        if self.markers:
            last_marker = self.markers.pop()
            self.graph_widget.removeItem(last_marker)
            self.click_locations.pop()
            print("Last selection removed")
        else:
            print("No selections to remove")

    # Save the found indices
    def save_indices(self):
        self.saved_indices = self.click_locations
        print("Data Keys Length")
        print(len(self.dataKeys))
        print(self.keyIndex)
        self.savedInflPointDict[self.dataKeys[self.keyIndex]] = self.saved_indices
        print(f"Indices saved: {self.saved_indices}")
        self.click_locations = []
        self.markers = []
        self.saved_indices = []

    # Pop up a message box to show what indices have been selected.
    def show_saved_indices(self):
        if self.saved_indices:
            QMessageBox.information(self, "Saved Indices", f"Saved indices: {self.saved_indices}")
        else:
            QMessageBox.information(self, "Saved Indices", "No indices saved yet.")

    # Ensure that all data is saved when the graph is closed.
    def closeEvent(self, event):
        
        if (len(self.savedInflPointDict.keys()) == 0 or self.dataKeys[self.keyIndex] not in self.savedInflPointDict.keys()):
            self.savedInflPointDict[self.dataKeys[self.keyIndex]] = self.click_locations

        print("Saving Inflection Point Data")
        file_path = "saved_inflection_point_dictionary.pkl"

        with open(file_path, 'wb') as f:
            pkl.dump(self.savedInflPointDict, f)

        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SignalGraphWindow()
    window.show()
    sys.exit(app.exec_())
