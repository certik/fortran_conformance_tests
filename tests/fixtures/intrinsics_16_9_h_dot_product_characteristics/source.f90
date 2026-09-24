! rule: S16.9.73-002
! covers: DOT_PRODUCT-numeric-result-expression-type-kind
! covers: DOT_PRODUCT-logical-result-and-kind
! covers: DOT_PRODUCT-result-scalar
program i169h_dot_product_characteristics
  implicit none
  integer :: ia(2)
  real(kind=kind(0.0d0)) :: rb(2)
  logical :: la(2), lb(2)
  integer :: checks
  checks = 0
  ia = [1, 2]; rb = [4.0d0, 8.0d0]
  la = [.true., .false.]; lb = [.false., .false.]
  call require('numeric DOT_PRODUCT result follows product expression kind', &
       kind(dot_product(ia, rb)) == kind(ia(1) * rb(1)), checks)
  call require('logical DOT_PRODUCT result has logical expression kind and value', &
       kind(dot_product(la, lb)) == kind(la(1) .and. lb(1)) .and. .not. dot_product(la, lb), checks)
  call require('DOT_PRODUCT result is scalar', size(shape(dot_product([1, 2], [3, 4]))) == 0, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DOT PRODUCT CHARACTERISTICS OK'
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
end program i169h_dot_product_characteristics
