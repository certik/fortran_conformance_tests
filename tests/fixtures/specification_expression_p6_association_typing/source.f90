module specification_expression_p6_provider
  implicit none
  integer :: use_n
end module specification_expression_p6_provider
module specification_expression_p6_host_scope
  implicit none
  integer :: host_n
contains
  subroutine observe_host(expected)
    integer, intent(in) :: expected
    integer :: a(host_n)
    if (size(a) /= expected) error stop 'SEP6:host-typing'
  end subroutine observe_host
end module specification_expression_p6_host_scope
program specification_expression_p6_association_typing
  use specification_expression_p6_provider, only: use_n
  use specification_expression_p6_host_scope, only: host_n, observe_host
  implicit none
  use_n=8
  call observe_use(8)
  host_n=4
  call observe_host(4)
  write(*,'(a)') 'SPECEXPR P6 ASSOCIATION TYPING OK'
contains
  subroutine observe_use(expected)
    use specification_expression_p6_provider, only: use_n
    integer, intent(in) :: expected
    integer :: a(use_n)
    if (size(a) /= expected) error stop 'SEP6:use-typing'
  end subroutine observe_use
end program specification_expression_p6_association_typing
