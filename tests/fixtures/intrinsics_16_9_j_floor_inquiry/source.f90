program intrinsics_16_9_j_floor_inquiry
  implicit none
  integer :: checks
  integer :: observed
  checks=0
  observed = floor(-3.25)
  if (observed /= -4) then
    write(*,'(a)') 'I16J:floor_inquiry:greatest-integer'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FLOOR INQUIRY OK'
end program intrinsics_16_9_j_floor_inquiry
