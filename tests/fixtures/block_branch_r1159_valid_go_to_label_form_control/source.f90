program go_to_label_form_control
implicit none
integer :: value
value=0
go to 100
value=-1
100 value=23
90 continue
if (value /= 23) error stop 1
write(*,'(a)') 'GO TO LABEL FORM OK'
end program go_to_label_form_control
