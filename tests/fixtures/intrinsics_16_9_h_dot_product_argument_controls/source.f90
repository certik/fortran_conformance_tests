! rule: S16.9.73-001
! covers: DOT_PRODUCT-vector-a-type-rank
! covers: DOT_PRODUCT-vector-b-compatible-type-rank
! covers: DOT_PRODUCT-vector-b-same-size
program i169h_dot_product_argument_controls
  implicit none
  integer :: checks
  integer :: ia(3), ib(3)
  logical :: la(2), lb(2)
  checks = 0
  ia = [1, 2, 3]; ib = [2, 3, 4]
  la = [.true., .false.]; lb = [.true., .true.]
  call require('DOT_PRODUCT vector A rank one admitted', dot_product([1, 2, 3], ib) == 20, checks)
  call require('DOT_PRODUCT compatible numeric and logical vector pairs admitted', &
       dot_product(ia, ib) == 20 .and. dot_product(la, lb), checks)
  call require('DOT_PRODUCT equal-size vectors contribute all elements', dot_product([1, 2, 3], [2, 3, 4]) == 20, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DOT PRODUCT ARGUMENT CONTROLS OK'
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
end program i169h_dot_product_argument_controls
