! rule: S16.9.77-007
! covers: EOSHIFT-positive-shift-element-mapping
! covers: EOSHIFT-negative-shift-element-mapping
! covers: EOSHIFT-array-valued-shift-indexing
! covers: EOSHIFT-boundary-used-outside-bounds
program i169h_eoshift_mapping_values
  implicit none
  integer :: checks
  integer :: v(4), m(3,3), r(3,3), sh(3), b(3)
  checks = 0
  v = [1, 2, 3, 4]
  m = reshape([1,2,3,4,5,6,7,8,9], [3,3])
  sh = [-1, 1, 0]; b = [91, 92, 93]
  r = eoshift(m, sh, b, dim=2)
  call require('EOSHIFT positive shift maps elements left', all(eoshift(v, 2, 99) == [3, 4, 99, 99]), checks)
  call require('EOSHIFT negative shift maps elements right', all(eoshift(v, -1, 99) == [99, 1, 2, 3]), checks)
  call require('EOSHIFT array-valued SHIFT indexes non-DIM subscripts', r(1,1) == 91 .and. r(2,3) == 92 .and. r(3,2) == 6, checks)
  call require('EOSHIFT boundary used outside bounds retained', &
       r(1,1) == 91 .and. r(2,3) == 92 .and. r(1,2) == 1, checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT MAPPING VALUES OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program i169h_eoshift_mapping_values
