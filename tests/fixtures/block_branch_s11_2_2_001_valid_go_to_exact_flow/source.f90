program go_to_exact_flow
implicit none
integer :: trace, skipped
trace=100
skipped=0
go to 200
skipped=-77
200 trace=trace+7
if (trace /= 107) error stop 1
if (skipped /= 0) error stop 2
write(*,'(a)') 'GO TO EXACT FLOW OK'
end program go_to_exact_flow
