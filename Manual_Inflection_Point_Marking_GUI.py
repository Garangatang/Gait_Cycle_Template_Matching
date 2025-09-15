"""
Description: This GUI can be used to manually mark a subsection of inflection points within underfoot pressure data.
    This subsection of data can be used to construct a template within Gait_Cycle_Template_Matching.py which can 
    find all inflection points within the larger dataset.

Written by Grange Simpson
Version: 2025.09.09

Usage: When you run the file a file selector will be opened. A Python dictionary containing key: dataset name, and
    value: numpy array dataset compressed into a pandas .pkl file is the only acceptable file type. Select the appropriate .pkl
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
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import os
import pandas as pd
import pickle as pkl
from pathlib import Path

class SignalGraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_size = 18
        self.font = QFont()
        self.font.setPointSize(self.font_size)
        self.font2 = QFont()
        self.font2.setPointSize(15)
        self.setWindowTitle("Manual Selection of Inflection Points")
        self.setStyleSheet("QLabel {font: {self.font_size}pt}")
        self.setGeometry(200, 200, 1600, 1200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create the graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.getAxis("bottom").setStyle(tickFont = self.font)
        self.graph_widget.getAxis("left").setStyle(tickFont = self.font)
        main_layout.addWidget(self.graph_widget)

        self.hs_click_locations = []
        # hs_Markers to show in the graph GUI
        self.hs_markers = []
        self.hs_saved_indices = []

        self.to_click_locations = []
        self.to_markers = []
        self.to_saved_indices = []

        # Dictionary for saving the inflection point indices with their data
        self.savedHSInflPointDict = {}
        self.savedTOInflPointDict = {}

        # Generate sample signal data
        self.normPressDict = {}
        self.x = None
        self.y = None
        self.keyIndex = None
        self.dataKeys = None
        self.upSampleVal = int(1980/33)
        self.dataLength = 1300*self.upSampleVal

        # Value to toggle between heel strike and toe off
        self.inflMarker = "Heel Strike"
        self.markerColor = 'y'

        if (self.x == None and self.y == None):
            self.TIP_file_path = None
            self.hs_file_path = None
            self.to_file_path = None
            self.hs_file_name = "GT_GUI_Parsing/hs_manually_parsed_data.pkl"
            self.to_file_name = "GT_GUI_Parsing/to_manually_parsed_data.pkl"
            self.check_files_exist()
            self.open_file_dialogue()
            self.load_pkl_file_data()
            self.update_graph_data_forward()

        # Enable mouse clicking on the plot
        self.graph_widget.scene().sigMouseClicked.connect(self.on_plot_click)

        # Create buttons
        
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        #self.clear_button = QPushButton("Clear All Selections")
        #self.clear_button.setFont(self.font)
        #self.clear_button.clicked.connect(self.clear_selections)
        #button_layout.addWidget(self.clear_button)

        self.hs_to_toggle_button = QPushButton("Heel Strike (yellow)")
        self.hs_to_toggle_button.setFont(self.font)
        self.hs_to_toggle_button.clicked.connect(self.hs_to_toggle)
        button_layout.addWidget(self.hs_to_toggle_button)

        self.save_button = QPushButton("Save Indices")
        self.save_button.setFont(self.font)
        self.save_button.clicked.connect(self.save_indices)
        button_layout.addWidget(self.save_button)

        # Switch the data graph back to the previous data seen
        self.update_graph_backward_button = QPushButton("Go Backward to Next Data Section")
        self.update_graph_backward_button.setFont(self.font)
        self.update_graph_backward_button.clicked.connect(self.change_data_to_mark_backward)
        button_layout.addWidget(self.update_graph_backward_button)

        # Switch the data graph back to the next data
        self.update_graph_forward_button = QPushButton("Go Forward to Next Data Section")
        self.update_graph_forward_button.setFont(self.font)
        self.update_graph_forward_button.clicked.connect(self.change_data_to_mark_forward)
        button_layout.addWidget(self.update_graph_forward_button)  
        
    def check_files_exist(self):
        TIP_file_path = Path("GT_GUI_Parsing/Upsamp_UP_Dict.pkl")
        hs_infl_file_path = Path(f"{self.hs_file_name}")
        to_infl_file_path = Path(f"{self.to_file_name}")

        if TIP_file_path.is_file():
            print(f"{TIP_file_path} exists in the current folder")
            self.TIP_file_path = TIP_file_path

        if hs_infl_file_path.is_file():
            print(f"{hs_infl_file_path} exists in the current folder")
            self.hs_file_path = hs_infl_file_path 
        
        if to_infl_file_path.is_file():
            print(f"{to_infl_file_path} exists in the current folder")
            self.to_file_path = to_infl_file_path

    def open_file_dialogue(self):
        # Skip dialogue if data already found
        if self.TIP_file_path != None:
            return
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", options=options)
        if file_name:
            self.TIP_file_path = file_name

    # Load data stored in pkl files for manual inflection point marking
    def load_pkl_file_data(self):
        self.dataDirectory = './'
        terrFileList = [f for f in os.listdir(self.dataDirectory) if f.endswith('.pkl')]
        # Default used is TIP_Dict.pkl
        with open(self.TIP_file_path, 'rb') as file:
            # Load the dictionary from the file
            self.normPressDict = pkl.load(file)

        self.dataKeys = list(self.normPressDict.keys())
        
        if self.hs_file_path != None:
            with open(self.hs_file_path, 'rb') as file:
                # Load the dictionary from the file
                self.savedHSInflPointDict = pkl.load(file)

        if self.to_file_path != None:
            with open(self.to_file_path, 'rb') as file:
                # Load the dictionary from the file
                self.savedTOInflPointDict = pkl.load(file)
        

    # Update the graph to new data
    def update_graph_data_forward(self):
        if (self.keyIndex == None):
            if self.hs_file_path != None:
                inflPointKeys = list(self.savedHSInflPointDict.keys())
                self.keyIndex = len(inflPointKeys) - 1

                # Set up the 
                self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), 
                                    len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
                self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()
                pen = pg.mkPen(color='m', width=3)
                self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)

                # Loading in datapoints if they already exist
                if self.dataKeys[self.keyIndex] in self.savedHSInflPointDict.keys():
                    currInds = self.savedHSInflPointDict[self.dataKeys[self.keyIndex]]
                    
                    for ind in currInds:
                        self.hs_click_locations.append(ind)
                        x = ind
                        y = self.y[x]
                        marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'y')
                        self.hs_markers.append(marker)

                # Loading in datapoints if they already exist
                if self.dataKeys[self.keyIndex] in self.savedTOInflPointDict.keys():
                    currInds = self.savedTOInflPointDict[self.dataKeys[self.keyIndex]]
                    
                    for ind in currInds:
                        self.to_click_locations.append(ind)
                        x = ind
                        y = self.y[x]
                        marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'cyan')
                        self.to_markers.append(marker)

            else:                         
                self.keyIndex = 0
                # Set up the 
                self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), 
                                    len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
                self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()

                pen = pg.mkPen(color='m', width=3)
                self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)

        elif (self.normPressDict != None and self.keyIndex < len(self.dataKeys) - 1):
            self.keyIndex += 1
            self.x = np.linspace(0, len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]), 
                                 len(self.normPressDict[self.dataKeys[self.keyIndex]].iloc[0:self.dataLength]))
            self.y = self.normPressDict[self.dataKeys[self.keyIndex]][self.normPressDict[self.dataKeys[self.keyIndex]].columns[0]].iloc[0:self.dataLength].to_numpy()
            # Showing previously clicked points if navigating backward.
            pen = pg.mkPen(color='m', width=3)
            self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)

            # Loading in datapoints if they already exist
            if self.dataKeys[self.keyIndex] in self.savedHSInflPointDict.keys():
                currInds = self.savedHSInflPointDict[self.dataKeys[self.keyIndex]]
                
                for ind in currInds:
                    self.hs_click_locations.append(ind)
                    x = ind
                    y = self.y[x]
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'y')
                    self.hs_markers.append(marker)

            # Loading in datapoints if they already exist
            if self.dataKeys[self.keyIndex] in self.savedTOInflPointDict.keys():
                currInds = self.savedTOInflPointDict[self.dataKeys[self.keyIndex]]
                
                for ind in currInds:
                    self.to_click_locations.append(ind)
                    x = ind
                    y = self.y[x]
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'cyan')
                    self.to_markers.append(marker)

        currentKey = list(self.dataKeys)[self.keyIndex]
        self.setWindowTitle("Manual Selection of Inflection Points " + currentKey + " " + str(self.keyIndex + 1) + "/" + str(len(self.dataKeys)))

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
            pen = pg.mkPen(color='m', width=3)
            self.plot = self.graph_widget.plot(self.x, self.y, pen = pen)

            # Loading in datapoints if they already exist
            if len(self.savedHSInflPointDict[self.dataKeys[self.keyIndex]]) != 0:
                currInds = self.savedHSInflPointDict[self.dataKeys[self.keyIndex]]
                
                for ind in currInds:
                    self.hs_click_locations.append(ind)
                    x = ind
                    y = self.y[x]
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'y')
                    self.hs_markers.append(marker)

            # Loading in datapoints if they already exist
            if len(self.savedTOInflPointDict[self.dataKeys[self.keyIndex]]) != 0:
                currInds = self.savedTOInflPointDict[self.dataKeys[self.keyIndex]]
                
                for ind in currInds:
                    self.to_click_locations.append(ind)
                    x = ind
                    y = self.y[x]
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= 'cyan')
                self.to_markers.append(marker)

            
        currentKey = list(self.dataKeys)[self.keyIndex]
        self.setWindowTitle("Manual Selection of Inflection Points " + currentKey + " " + str(self.keyIndex + 1) + "/" + str(len(self.dataKeys)))
        
    # Move to the next dataset to mark.    
    def change_data_to_mark_forward(self):
        self.graph_widget.clear()
        self.save_indices()
        self.update_graph_data_forward()
        

    # Move to the previous dataset to mark
    def change_data_to_mark_backward(self):
        self.graph_widget.clear()
        self.save_indices()
        self.update_graph_data_backward()

    # Flow for methods when the graph is clicked.
    def on_plot_click(self, event):
        pos = event.scenePos()
        if self.inflMarker == "Heel Strike":
            if self.graph_widget.sceneBoundingRect().contains(pos):
                mouse_point = self.graph_widget.plotItem.vb.mapSceneToView(pos)
                clicked_x, clicked_y = mouse_point.x(), mouse_point.y()
                #pos = event.scenePos()
                index = self.find_nearest_point(clicked_x, clicked_y)
                
                if index is not None:
                    x, y = self.x[index], self.y[index]
                    minLastClickedPointDist = np.abs(self.hs_click_locations - index)
                    # Clearing point if click is near another previously selected point
                    if (len(minLastClickedPointDist) > 0 and min(minLastClickedPointDist) < 15*self.upSampleVal):
                        minLocation = np.array(minLastClickedPointDist).argmin()
                        #print("hs_Markers")
                        #print(self.hs_markers)
                        del_marker = self.hs_markers[minLocation]
                        self.graph_widget.removeItem(del_marker)
                        del self.hs_click_locations[minLocation]
                        del self.hs_markers[minLocation]
                    
                    # Adding clicked point to the graph
                    else:
                        self.hs_click_locations.append(index)
                        marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= self.markerColor)
                        self.hs_markers.append(marker)

                    print(self.inflMarker)
                    print(f"Clicked at index: {index}, x={x:.2f}, y={y:.2f}")       
                    print(self.hs_click_locations)  

        else:
            mouse_point = self.graph_widget.plotItem.vb.mapSceneToView(pos)
            clicked_x, clicked_y = mouse_point.x(), mouse_point.y()
            #pos = event.scenePos()
            index = self.find_nearest_point(clicked_x, clicked_y)
            
            if index is not None:
                x, y = self.x[index], self.y[index]
                minLastClickedPointDist = np.abs(self.to_click_locations - index)
                # Clearing point if click is near another previously selected point
                if (len(minLastClickedPointDist) > 0 and min(minLastClickedPointDist) < 15*self.upSampleVal):
                    minLocation = np.array(minLastClickedPointDist).argmin()
                    #print("hs_Markers")
                    #print(self.hs_markers)
                    del_marker = self.to_markers[minLocation]
                    self.graph_widget.removeItem(del_marker)
                    del self.to_click_locations[minLocation]
                    del self.to_markers[minLocation]
                
                # Adding clicked point to the graph
                else:
                    self.to_click_locations.append(index)
                    marker = self.graph_widget.plot([x], [y], pen=None, symbol='o', symbolSize=6, symbolBrush= self.markerColor)
                    self.to_markers.append(marker)

                print(self.inflMarker)
                print(f"Clicked at index: {index}, x={x:.2f}, y={y:.2f}")       
                print(self.to_click_locations)  

    # Map the click onto the graph if click is close enough.
    def find_nearest_point(self, clicked_x, clicked_y):
        index = np.argmin(np.abs(self.x - clicked_x))
        y_tolerance = 0.2
        if abs(self.y[index] - clicked_y) <= y_tolerance:
            return index
        return None

    # Clear all selections made on the graph.
    def clear_selections(self):
        if self.inflMarker == "Heel Strike":
            for marker in self.hs_markers:
                self.graph_widget.removeItem(marker)
            self.hs_markers.clear()
            self.hs_click_locations.clear()
        else:
            for marker in self.to_markers:
                self.graph_widget.removeItem(marker)
            self.to_markers.clear()
            self.to_click_locations.clear()
            print("All selections cleared")

    def hs_to_toggle(self):
        current_text = self.hs_to_toggle_button.text()
        if "Heel Strike" in current_text:
            self.inflMarker = 'Toe Off'
            self.hs_to_toggle_button.setText(self.inflMarker + " (cyan)")
            self.markerColor = 'cyan'
            

        else:
            self.inflMarker = "Heel Strike"
            self.hs_to_toggle_button.setText(self.inflMarker + " (yellow)")
            self.markerColor = 'y'
            

    # Remove the last selection made.
    def remove_last_selection(self):
        if self.inflMarker == 'Heel Strike':
            if self.hs_markers:
                last_marker = self.to_markers.pop()
                self.graph_widget.removeItem(last_marker)
                self.hs_click_locations.pop()
                print("Last selection removed")
            else:
                print("No selections to remove")
        else:
            if self.to_markers:
                last_marker = self.to_markers.pop()
                self.graph_widget.removeItem(last_marker)
                self.to_click_locations.pop()
                print("Last selection removed")
            else:
                print("No selections to remove")

    # Save the found indices
    def save_indices(self):
        self.hs_saved_indices = self.hs_click_locations
        print("Data Keys Length")
        print(len(self.dataKeys))
        print(self.keyIndex)
        self.savedHSInflPointDict[self.dataKeys[self.keyIndex]] = self.hs_saved_indices
        print(f"Indices saved: {self.hs_saved_indices}")
        self.hs_click_locations = []
        self.hs_markers = []
        self.hs_saved_indices = []

        self.to_saved_indices = self.to_click_locations
        print("Data Keys Length")
        print(len(self.dataKeys))
        print(self.keyIndex)
        self.savedTOInflPointDict[self.dataKeys[self.keyIndex]] = self.to_saved_indices
        print(f"Indices saved: {self.to_saved_indices}")
        self.to_click_locations = []
        self.to_markers = []
        self.to_saved_indices = []

    # Pop up a message box to show what indices have been selected.
    def show_hs_saved_indices(self):
        if self.hs_saved_indices:
            QMessageBox.information(self, "Saved Indices", f"Saved indices: {self.hs_saved_indices}")
        else:
            QMessageBox.information(self, "Saved Indices", "No indices saved yet.")

    # Ensure that all data is saved when the graph is closed.
    def closeEvent(self, event):
        self.save_indices()
        if (len(self.savedHSInflPointDict.keys()) == 0 or self.dataKeys[self.keyIndex] not in self.savedHSInflPointDict.keys()):
            self.savedHSInflPointDict[self.dataKeys[self.keyIndex]] = self.hs_click_locations

        print("Saving Inflection Point Data")
        TIP_file_path = f"{self.hs_file_name}"

        with open(TIP_file_path, 'wb') as f:
            pkl.dump(self.savedHSInflPointDict, f)

        if (len(self.savedTOInflPointDict.keys()) == 0 or self.dataKeys[self.keyIndex] not in self.savedTOInflPointDict.keys()):
            self.savedTOInflPointDict[self.dataKeys[self.keyIndex]] = self.to_click_locations

        print("Saving Inflection Point Data")
        TIP_file_path = f"{self.to_file_name}"

        with open(TIP_file_path, 'wb') as f:
            pkl.dump(self.savedTOInflPointDict, f)

        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SignalGraphWindow()
    window.show()
    sys.exit(app.exec_())
