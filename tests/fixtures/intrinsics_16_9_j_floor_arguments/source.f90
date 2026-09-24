program intrinsics_16_9_j_floor_arguments
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(12)
  integer, parameter :: rk = kind(0.0d0)
  real(rk) :: high
  integer(ik) :: selected
  checks=0
  high = 5.75_rk
  selected = floor(high, kind=ik)
  if (selected /= 5_ik) then
    write(*,'(a)') 'I16J:floor_arguments:real-a'
    error stop
  end if
  checks=checks+1
  if (kind(floor(high, kind=ik)) /= ik) then
    write(*,'(a)') 'I16J:floor_arguments:constant-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FLOOR ARGUMENTS OK'
end program intrinsics_16_9_j_floor_arguments
