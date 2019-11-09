import java.io.*;
import java.net.*;
import java.time.Duration;
import java.time.Instant;

public class sender {
    static int windowsSize = 10;
    static int bufferSize = 500;
    static File file;
    static FileInputStream fileinputstream;
    static String emulatorHostAddr;
    static int emulatorUDPPort;
    static int senderUDPPort;
    static PrintWriter seqnumLog;
    static PrintWriter ackLog;
    static PrintWriter timeLog;
//    static int lengthOfLastPackage = 0;


    public static void main(String[] args) throws Exception {
        // input check
        if (args.length != 4) {
            System.err.println("Invalid input: ./sender <ip adress> <prot to> <port from> <file name>");
            System.exit(1);
        }

        // read from file that want to send
        file = new File(args[3]);
        byte lines[] = new byte [(int) file.length()];
        fileinputstream = new FileInputStream(file);
        fileinputstream.read(lines);


        // prepare the packets which divide the package into different part and stored into packets.
        // file.length == lines.length
        int numPackage = (int) (file.length() / bufferSize);
        // last package is not fully devide by 500, then add extra 1 in number of package
        if (lines.length % bufferSize != 0) {
            numPackage += 1;
//            lengthOfLastPackage = (int) lines.length % bufferSize);
        }
        packet packets[] = new packet[numPackage];
        int transferedSize = 0;
        for (int i = 0; i < numPackage; i++) {
            byte copyData[] = new byte[Math.min(bufferSize, lines.length - transferedSize)];
            System.arraycopy(lines, transferedSize, copyData, 0, Math.min(bufferSize, lines.length - transferedSize));
            // sequence number: module 32
            packets[i] = packet.createPacket(i % 32, new String(copyData));
            transferedSize += bufferSize;
        }


        // init
        emulatorUDPPort = Integer.parseInt(args[1]);
        senderUDPPort = Integer.parseInt(args[2]);
        DatagramSocket senderSocket = new DatagramSocket();
        DatagramSocket recvSocket = new DatagramSocket(senderUDPPort);
        InetAddress IPAddress = InetAddress.getByName(args[0]);
        seqnumLog= new PrintWriter(new FileWriter("./seqnum.log"));
        ackLog = new PrintWriter(new FileWriter("./ack.log"));
        timeLog = new PrintWriter(new FileWriter("./time.log"));
        int windowsBase = 0;
        int nextPacket = 0;
        int timeOut = 500;

        Instant start = Instant.now();
        //send the data in each windows size
        while (windowsBase != numPackage) {

            // send whole windows (check if less than windows size, then sent)
            while (nextPacket < windowsBase + windowsSize && nextPacket < numPackage) {
                byte[] sendData = packets[nextPacket].getUDPdata();
                DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length,
                        IPAddress, emulatorUDPPort);
                senderSocket.send(sendPacket);
                seqnumLog.println(nextPacket % 32);
                nextPacket++;
            }
            // recieve for server and move the windows
            try {
                // set the timeout to 500
                recvSocket.setSoTimeout(timeOut);
                // create ack reciving packet
                byte[] ack = new byte[1024];
                DatagramPacket recvPacket = new DatagramPacket(ack, ack.length);
                recvSocket.receive(recvPacket);
                packet ackPacket = packet.parseUDPdata(recvPacket.getData());
                ackLog.println(ackPacket.getSeqNum());
                if (ackPacket.getSeqNum() == windowsBase % 32) {
                    // first packet in windowsbase
                    windowsBase++;
                } else if (ackPacket.getSeqNum() > windowsBase % 32 &&
                        (ackPacket.getSeqNum() - windowsBase % 32) < windowsSize) {
                    // packet within windowsSize, since cumulative, so add windowsSize
                    windowsBase += ackPacket.getSeqNum() - windowsBase % 32 + 1;
                } else if (ackPacket.getSeqNum() < windowsSize &&
                        (ackPacket.getSeqNum() + 32 - windowsBase % 32 < windowsSize) ){
                    windowsBase += ackPacket.getSeqNum() + 32 - windowsBase % 32 + 1;
                }
            } catch (SocketTimeoutException e) {
                // lost all packet
                for (int i = windowsBase; i < nextPacket; i++) {
                    byte[] sendData = packets[i].getUDPdata();
                    DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length,
                            IPAddress, emulatorUDPPort);
                    senderSocket.send(sendPacket);
                    seqnumLog.println(i % 32);
                }

            }

        }

        // finished all package send EOT

        packet EOT = packet.createEOT(numPackage);
        byte[] eotData = EOT.getUDPdata();
        DatagramPacket eotPacket = new DatagramPacket(eotData, eotData.length,
                IPAddress, emulatorUDPPort);
        senderSocket.send(eotPacket);
        seqnumLog.println(EOT.getSeqNum());
        while(true){ // exit after EOT from receiver
            try{
                byte[] arkRecv = new byte[1024];
                DatagramPacket recvPacket = new DatagramPacket(arkRecv, arkRecv.length);
                recvSocket.receive(recvPacket);
                packet pk = packet.parseUDPdata(recvPacket.getData());
                // 2 means it is EOT
                if (pk.getType() == 2) break;
            } catch (SocketTimeoutException e) {
                continue;
            }

        }
        // calculate the time and print on time.log
        Instant end = Instant.now();
        Duration timeElapsed = Duration.between(start, end);
        timeLog.println(timeElapsed.toMillis());

        //closing
        senderSocket.close();
        recvSocket.close();
        seqnumLog.close();
        ackLog.close();
        timeLog.close();

    }

}