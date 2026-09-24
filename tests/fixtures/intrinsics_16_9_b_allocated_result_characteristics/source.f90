program intrinsics_16_9_b_allocated_result_characteristics
  implicit none
  integer :: checks
  integer, allocatable :: array(:)
  logical :: status
  checks=0
  allocate(array(3))
  status = allocated(array)
  if (kind(allocated(array)) /= kind(.false.)) then
    write(*,'(a)') 'I16B:allocated_result_characteristics:default-logical-kind'
    error stop
  end if
  checks=checks+1
  associate (scalar_probe => allocated(array))
  if (rank(scalar_probe) /= 0) then
      write(*,'(a)') 'I16B:allocated_result_characteristics:scalar-rank'
      error stop
    end if
    checks=checks+1
    end associate
  if (.not. status) then
    write(*,'(a)') 'I16B:allocated_result_characteristics:scalar-result'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16B:allocated_result_characteristics:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ALLOCATED RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_b_allocated_result_characteristics
