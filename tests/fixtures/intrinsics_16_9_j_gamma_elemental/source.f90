program intrinsics_16_9_j_gamma_elemental
  implicit none
  integer :: checks
  real :: values(3)
  checks=0
  values = [1.0, 1.5, -0.5]
  if (any(shape(gamma(values)) /= [3])) then
    write(*,'(a)') 'I16J:gamma_elemental:elementwise-shape'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J GAMMA ELEMENTAL OK'
end program intrinsics_16_9_j_gamma_elemental
