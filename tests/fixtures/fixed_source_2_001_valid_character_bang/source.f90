      program p                                                         
      implicit none                                                     
      character(len=3) :: text, record                                  
      integer :: ios                                                    
      text='???'                                                        
      record='???'                                                      
      ios=99                                                            
      text='a!b'                                                        
      write(record,10,iostat=ios)                                       
      if (ios/=0) error stop 1                                          
      if (text(1:1)/='a'.or.text(3:3)/='b') error stop 2                
      if (text(2:2)/='!') error stop 3                                  
      if (record(1:1)/='a'.or.record(3:3)/='b') error stop 4            
      if (record(2:2)/='!') error stop 5                                
   10 format('a!b')                                                     
      end program p                                                     
