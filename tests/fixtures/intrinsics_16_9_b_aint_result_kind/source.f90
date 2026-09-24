program intrinsics_16_9_b_aint_result_kind
  implicit none
  integer :: checks
  real(kind=kind(0.0d0)) :: high
  real :: value
  checks=0
  high = 2.0d0
  value = aint(2.5)
  if (value /= 2.0) then
    write(*,'(a)') 'I16B:aint_result_kind:real-result-value'
    error stop
  end if
  checks=checks+1
  if (kind(aint(high, kind=kind(0.0))) /= kind(0.0)) then
    write(*,'(a)') 'I16B:aint_result_kind:kind-present'
    error stop
  end if
  checks=checks+1
  if (kind(aint(high)) /= kind(high)) then
    write(*,'(a)') 'I16B:aint_result_kind:kind-absent'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16B:aint_result_kind:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B AINT RESULT KIND OK'
end program intrinsics_16_9_b_aint_result_kind
