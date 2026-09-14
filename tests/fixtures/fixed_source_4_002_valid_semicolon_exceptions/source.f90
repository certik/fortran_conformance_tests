      program p                                                         
      implicit none                                                     
      character(len=3) :: text, record                                  
      integer :: ios, x                                                 
      text='???'                                                        
      record='???'                                                      
      ios=99                                                            
      x=0                                                               
      text='a;b'! ;x=99                                                 
      write(record,10,iostat=ios)                                       
      if (ios/=0) error stop 1                                          
      if (text(1:1)/='a'.or.text(3:3)/='b') error stop 2                
      if (text(2:2)/=';') error stop 3                                  
      if (record(1:1)/='a'.or.record(3:3)/='b') error stop 4            
      if (record(2:2)/=';') error stop 5                                
      x=1                                                               
     ;+2                                                                
      if (x/=3) error stop 6                                            
   10 format('a;b')                                                     
      end program p                                                     
