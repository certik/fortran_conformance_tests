program intrinsics_16_9_j_findloc_mask_argument
  implicit none
  integer :: checks
  integer :: grid(2,3)
  logical :: mask(2,3), all_true(2,3)
  integer, allocatable :: hit(:)
  checks=0
  grid = reshape([0, 3, 7, 4, 7, 6], [2,3])
  mask = reshape([.false., .false., .false., .false., .true., .false.], [2,3])
  all_true = .true.
  hit = findloc(grid, 7, mask=mask)
  if (any(hit /= [1, 3])) then
    write(*,'(a)') 'I16J:findloc_mask_argument:logical-conformable-mask'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC MASK ARGUMENT OK'
end program intrinsics_16_9_j_findloc_mask_argument
