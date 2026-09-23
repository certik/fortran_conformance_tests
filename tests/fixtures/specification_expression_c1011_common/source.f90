program specification_expression_c1011_common
  implicit none
  integer :: n_common
  common /specblk/ n_common
  n_common=5
  call observe(5)
  n_common=2
  call observe(2)
  write(*,'(a)') 'SPECEXPR C1011 COMMON OK'
contains
  subroutine observe(expected)
    integer, intent(in) :: expected
    integer :: n_common
    common /specblk/ n_common
    integer :: a(n_common)
    if (size(a) /= expected) error stop 'SEC1011:common'
  end subroutine observe
end program specification_expression_c1011_common
