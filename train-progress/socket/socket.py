import threading
import socket
import time


# conn=result[0]
# address=result[1]
def server():
    socket_server=socket.socket()
    socket_server.bind(("localhost",8888))
    socket_server.listen(1)
    conn,address=socket_server.accept()
    print(f"接收到客户端连接,{address}")
    while 1:
        data:str=conn.recv(1024).decode("UTF-8")
        print(f"客户端发来的消息：{data}")

        msg=input("请输入你和客户端回复的消息：")
        if msg=='exit':
            break
        conn.send(msg.encode("UTF-8"))
    conn.close()
    socket_server.close()



def client():
    time.sleep(1)
    socket_client=socket.socket()
    socket_client.connect(("localhost",8888))
    time.sleep(2)
    while 1:
        meg=input("请输入：")
        socket_client.send(meg.encode("UTF-8"))
        recv_data = socket_client.recv(1024)
        print(f"服务端回复的消息：{recv_data.decode('UTF-8')}")
    socket_client.close()

if __name__ =="__main__":
    server_thread=threading.Thread(target=server)
    client_thread=threading.Thread(target=client)
    server_thread.start()
    client_thread.start()























# import time
# import threading

# def sing():
#     while 1:
#         print("我在唱歌，啦啦啦。。。。")
#         time.sleep(1)


# def dance():
#     while 1:
#         print("我在跳舞，嘿嘿嘿。。。。")
#         time.sleep(1)

# if __name__ =='__main__':
#     sing_thread=threading.Thread(target=sing)
#     dance_thread=threading.Thread(target=dance)

#     sing_thread.start()
#     dance_thread.start()



# def outer(func):
#     def inner():
#         print("我要水饺了")
#         func()
#         print("我要起床了")
#     return inner

# @outer
# def sleep():
#     import random
#     import time
#     print("水饺中")
#     time.sleep(random.randint(1,5))

# sleep()







# def account_create(initial_amount=0):
#     def atm (num,deposit=True):
#         nonlocal initial_amount
#         if deposit:
#             initial_amount+=num
#             print(f"存款+{num},账户余额：{initial_amount}")
#         else:
#             initial_amount-=num
#             print(f"取款：-{num},账户余额：{initial_amount}")
#     return atm

# atm=account_create()
# atm(400)
# atm(200,0)
# atm(500)





















