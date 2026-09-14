program character_blanks
implicit none
character(len=8) :: a, b
character(len=7) :: record
character(len=5) :: data
integer :: ios
a='?'
b='?'
record='?'
data='?'
ios=-1
a='ab  &   
    &  cd'
b="ef  &   
    &  gh"
if (a /= 'ab    cd') error stop 1
if (b /= 'ef    gh') error stop 2
if (a(3:6) /= ' ' .or. a(7:8) /= 'cd') error stop 6
if (b(3:6) /= ' ' .or. b(7:8) /= 'gh') error stop 7
data='A&&
&!;B'
if (data /= 'A&!;B') error stop 3
if (iachar(data(2:2)) /= 38) error stop 8
if (iachar(data(3:3)) /= 33) error stop 9
if (iachar(data(4:4)) /= 59) error stop 10
write(record,100,iostat=ios)
if (ios /= 0) error stop 4
if (record /= 'ij    k') error stop 5
if (record(3:6) /= ' ' .or. record(7:7) /= 'k') error stop 11
100 format('ij  &   
    &  k')
print '(A)', 'OK'
end program
