program intrinsics_16_9_b_any_result_values
  implicit none
  integer :: checks
  logical :: has_true(3), all_false(3), empty(0), mask2(2,3)
  logical, allocatable :: reduced(:)
  checks=0
  has_true = [.false., .true., .false.]
  all_false = [.false., .false., .false.]
  mask2 = reshape([.false., .false., .true., .false., .false., .true.], [2,3])
  if (.not. any(has_true)) then
    write(*,'(a)') 'I16B:any_result_values:any-true'
    error stop
  end if
  checks=checks+1
  if (any(all_false)) then
    write(*,'(a)') 'I16B:any_result_values:none-true-false'
    error stop
  end if
  checks=checks+1
  if (any(empty)) then
    write(*,'(a)') 'I16B:any_result_values:zero-size-false'
    error stop
  end if
  checks=checks+1
  reduced = any(mask2, dim=1)
  if (any(reduced .neqv. [.false., .true., .true.])) then
    write(*,'(a)') 'I16B:any_result_values:dim-sections'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'I16B:any_result_values:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ANY RESULT VALUES OK'
end program intrinsics_16_9_b_any_result_values
