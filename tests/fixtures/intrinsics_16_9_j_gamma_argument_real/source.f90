program intrinsics_16_9_j_gamma_argument_real
  implicit none
  integer :: checks
  integer, parameter :: rk = kind(0.0d0)
  real(rk) :: high
  checks=0
  high = 1.5_rk
  if (kind(gamma(high)) /= kind(high)) then
    write(*,'(a)') 'I16J:gamma_argument_real:real-x'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J GAMMA ARGUMENT REAL OK'
end program intrinsics_16_9_j_gamma_argument_real
