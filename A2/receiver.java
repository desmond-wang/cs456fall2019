import java.io.*;
import java.net.*;

public class receiver {
    static int emulatorUDPPort;
    static String fileName;

    public static void main(String[] args) throws Exception {
        if (args.length != 4) {
            System.err.println("Usage: ./receiver <host> <port to> <port from> <file>");
            System.exit(1);
        }

        // init
        emulatorUDPPort = Integer.parseInt(args[1]);
        InetAddress IPAddress = InetAddress.getByName(args[0]);
        DatagramSocket ackSocket = new DatagramSocket(emulatorUDPPort);
        DatagramSocket dataSocket = new DatagramSocket(Integer.parseInt(args[2]));
        fileName = args[3];
        PrintWriter dataWriter = new PrintWriter(new FileWriter(fileName));
        PrintWriter arrivalWriter = new PrintWriter(new FileWriter("./arrival.log"));

        int nextPacket = 0;
        byte[] recvData = new byte[1024];
        DatagramPacket recvPacket = new DatagramPacket(recvData, recvData.length);
        // open and continue recieve data until recieve eot.
        while (true) {
            dataSocket.receive(recvPacket);
            packet dataPacket = packet.parseUDPdata(recvPacket.getData());
            arrivalWriter.println(dataPacket.getSeqNum());
            if (nextPacket == dataPacket.getSeqNum()) {
                if (dataPacket.getType() == 2) {
                    // recieved eot, send back eot and close
                    packet eot = packet.createEOT(dataPacket.getSeqNum());
                    byte[] eotData = eot.getUDPdata();
                    DatagramPacket eotPacket = new DatagramPacket(eotData, eotData.length,
                            IPAddress, emulatorUDPPort);
                    ackSocket.send(eotPacket);

                    //close
                    ackSocket.close();
                    dataSocket.close();
                    dataWriter.close();
                    arrivalWriter.close();
                    return;
                }

                // normal data, write to disk
                dataWriter.print(new String(dataPacket.getData()));

                // send ack
                packet ack = packet.createACK(dataPacket.getSeqNum());
                byte[] ackData = ack.getUDPdata();
                DatagramPacket ackPacket = new DatagramPacket(ackData, ackData.length,
                        IPAddress, emulatorUDPPort);
                ackSocket.send(ackPacket);
                nextPacket++;
                nextPacket %= 32;
            } else {
                // wrong package, ack last correct one
                packet nack = packet.createACK((nextPacket + 31) % 32);
                byte[] nackData = nack.getUDPdata();
                DatagramPacket nackPacket = new DatagramPacket(nackData, nackData.length,
                        IPAddress, emulatorUDPPort);
                ackSocket.send(nackPacket);

            }
        }
    }
}