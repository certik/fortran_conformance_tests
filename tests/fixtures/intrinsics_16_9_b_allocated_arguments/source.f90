program intrinsics_16_9_b_allocated_arguments
  implicit none
  integer :: checks
  integer, allocatable :: array(:), scalar
  logical :: array_status, scalar_status
  checks=0
  allocate(array(2))
  array_status = allocated(array)
  scalar_status = allocated(scalar)
  if (.not. array_status) then
    write(*,'(a)') 'I16B:allocated_arguments:array-argument'
    error stop
  end if
  checks=checks+1
  if (scalar_status) then
    write(*,'(a)') 'I16B:allocated_arguments:scalar-argument'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:allocated_arguments:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ALLOCATED ARGUMENTS OK'
end program intrinsics_16_9_b_allocated_arguments
