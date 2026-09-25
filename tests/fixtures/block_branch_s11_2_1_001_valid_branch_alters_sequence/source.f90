program branch_alters_sequence
implicit none
integer :: trace
trace=10
go to 100
trace=-99
100 trace=trace+5
if (trace /= 15) error stop 1
write(*,'(a)') 'BRANCH ALTER SEQUENCE OK'
end program branch_alters_sequence
