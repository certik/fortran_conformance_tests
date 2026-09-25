program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -1
read(rec,'(I1)',delim='QUOTE') value
end program p
