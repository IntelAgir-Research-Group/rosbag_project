# python3 extract_graph.py bagfile
# python3 extract_graph.py SLAM_2021-06-03-12-32-22.bag
# python3 extract_graph.py turtlesim1.bag

from bagpy import bagreader
import pandas as pd
import sys
import ast
from graphviz import Digraph


bagfile = sys.argv[1]
bagname = bagfile.replace('.bag','')
b = bagreader(bagfile)

# topics into dataFrame for extraction to generate graph
topics = pd.DataFrame(b.topics, columns=['Topics'])
# print(topics)

# list of csv files based on the topics
csvfiles = []
for t in b.topics:
    data = b.message_by_topic(t)
    # print(data)
    csvfiles.append(data)

# merge files and only keep needed columns
df = pd.read_csv(bagname + '/rosout.csv')
df2 = pd.read_csv(bagname + '/rosout_agg.csv')
df = pd.concat([df, df2]).reset_index()
all_info = df[['name', 'msg', 'topics']]


graph = Digraph(name=bagname, strict=True)

# nodes
nodes = df['name'].unique()
for node in nodes:
    graph.node(node, node, {'shape': 'oval'})

all_topics = topics['Topics'].values.tolist()
sub_topics = []
for i in range(len(all_topics)):
    sub_topics += all_topics[i].split('/')[1:]

for sub_topic in sub_topics:
    if sub_topics.count(sub_topic) > 1 :
        substring = '/' + sub_topic
        # create clusters
        with graph.subgraph(name='cluster_' + sub_topic) as sub_topic:
            for topic in all_topics:
                if substring in topic:
                    sub_topic.node(topic, topic, {'shape': 'rectangle'})
            sub_topic.attr(label=substring)

# topics
topics = topics['Topics'].values.tolist()
for topic in topics:
    if topic not in graph:
        graph.node(topic, topic, {'shape': 'rectangle'})

# merge subscribers for each node
edge_info = pd.DataFrame(data={'name': nodes}, columns=['name', 'topics'])
list_of_topics = []
for i in range(len(nodes)):
    for j in range(len(all_info)):
        # merge topics with the same node name
        if all_info['name'][j] == nodes[i]:
            # evaluate string as list and merge them into one list
            list_of_topics += ast.literal_eval(all_info['topics'][j])
    # keep the unique value in the list of topics
    edge_info['topics'][i] = list(set(list_of_topics))

# edges
for i in range(len(nodes)):
    publisher = nodes[i]
    for j in range(len(edge_info['topics'][i])):
        subscriber = edge_info['topics'][i][j]
        graph.edge(publisher, subscriber)

# msg in both rosout and rosout_agg
substring = "Subscribing to "
for i in range(len(all_info['msg'])):
    if substring in all_info['msg'].iloc[i]:
        publisher = all_info['msg'].iloc[i].split(substring)[1]
        subscriber = all_info['name'].iloc[i]
        graph.edge(publisher, subscriber)

# msg in rosout_agg
# substring = "Subscribing to "
# for i in range(len(df2['msg'])):
#     if substring in df2['msg'].iloc[i]:
#         publisher = df2['msg'].iloc[i].split(substring)[1]
#         subscriber = df2['name'].iloc[i]
#         graph.edge(publisher, subscriber)

# add fixed node and edges
graph.node("/fixed node", "/rosout", {'shape': 'oval'})
graph.edge("/rosout", "/fixed node")
graph.edge("/fixed node", "/rosout_agg")

# generate graph
graph.view()