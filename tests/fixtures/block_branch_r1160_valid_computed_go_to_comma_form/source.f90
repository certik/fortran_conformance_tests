program computed_go_to_comma_form
implicit none
integer :: value, selector
selector=2
value=-1
go to (100,200), selector
value=-9
go to 300
100 value=11
go to 300
200 value=22
300 if (value /= 22) error stop 1
write(*,'(a)') 'COMPUTED GO TO COMMA OK'
end program computed_go_to_comma_form
