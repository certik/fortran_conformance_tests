program intrinsics_16_9_j_findloc_signature_options
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(12)
  integer :: grid(2,3)
  logical :: mask(2,3)
  integer(ik), allocatable :: masked_back(:)
  integer, allocatable :: positional(:), dimmed(:)
  checks=0
  grid = reshape([1, 2, 7, 4, 7, 6], [2,3])
  mask = reshape([.false., .true., .true., .false., .true., .true.], [2,3])
  positional = findloc(grid, 7)
  if (any(positional /= [1, 2])) then
    write(*,'(a)') 'I16J:findloc_signature_options:positional-array-value'
    error stop
  end if
  checks=checks+1
  masked_back = findloc(array=grid, value=7, mask=mask, kind=ik, back=.true.)
  if (any(masked_back /= [1_ik, 3_ik])) then
    write(*,'(a)') 'I16J:findloc_signature_options:named-optional-arguments'
    error stop
  end if
  checks=checks+1
  dimmed = findloc(grid, 7, dim=1, mask=mask)
  if (any(dimmed /= [0, 1, 1])) then
    write(*,'(a)') 'I16J:findloc_signature_options:dim-mask-branch'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC SIGNATURE OPTIONS OK'
end program intrinsics_16_9_j_findloc_signature_options
