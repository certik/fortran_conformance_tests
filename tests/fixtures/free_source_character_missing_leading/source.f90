program character_marker
implicit none
character(len=4) :: text
text='?'
text='ab&
cd'
if (text /= 'abcd') error stop 1
end program
