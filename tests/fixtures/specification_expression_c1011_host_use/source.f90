module specification_expression_provider
  implicit none
  integer :: use_n
end module specification_expression_provider
module specification_expression_host_scope
  implicit none
  integer :: host_n
contains
  subroutine observe_host(expected)
    integer, intent(in) :: expected
    integer :: a(host_n)
    if (size(a) /= expected) error stop 'SEC1011:host'
  end subroutine observe_host
end module specification_expression_host_scope
program specification_expression_c1011_host_use
  use specification_expression_provider, only: use_n
  use specification_expression_host_scope, only: host_n, observe_host
  implicit none
  use_n=8
  call observe_use(8)
  host_n=4
  call observe_host(4)
  write(*,'(a)') 'SPECEXPR C1011 HOST USE OK'
contains
  subroutine observe_use(expected)
    use specification_expression_provider, only: use_n
    integer, intent(in) :: expected
    integer :: a(use_n)
    if (size(a) /= expected) error stop 'SEC1011:use'
  end subroutine observe_use
end program specification_expression_c1011_host_use
