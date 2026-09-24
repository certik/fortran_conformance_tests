program intrinsics_16_9_b_aint_arguments
  implicit none
  integer :: checks
  real(kind=kind(0.0d0)) :: high
  real :: observed
  checks=0
  high = 2.5d0
  observed = aint(2.5)
  if (observed /= 2.0) then
    write(*,'(a)') 'I16B:aint_arguments:real-argument'
    error stop
  end if
  checks=checks+1
  observed = aint(high, kind=kind(0.0))
  if (kind(aint(high, kind=kind(0.0))) /= kind(0.0)) then
    write(*,'(a)') 'I16B:aint_arguments:constant-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:aint_arguments:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B AINT ARGUMENTS OK'
end program intrinsics_16_9_b_aint_arguments
