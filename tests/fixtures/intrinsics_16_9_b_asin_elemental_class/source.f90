program intrinsics_16_9_b_asin_elemental_class
  implicit none
  integer :: checks
  real :: inputs(3), values(3)
  checks=0
  inputs = [-1.0, 0.0, 1.0]
  values = asin(inputs)
  if (any(shape(values) /= [3])) then
    write(*,'(a)') 'I16B:asin_elemental_class:shape-preserved'
    error stop
  end if
  checks=checks+1
  if (values(1) >= 0.0 .or. values(3) <= 0.0) then
    write(*,'(a)') 'I16B:asin_elemental_class:position-signs'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asin_elemental_class:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIN ELEMENTAL CLASS OK'
end program intrinsics_16_9_b_asin_elemental_class
