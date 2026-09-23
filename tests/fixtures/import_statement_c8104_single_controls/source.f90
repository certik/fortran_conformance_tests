program import_statement_forms
  implicit none
  integer :: host_a, host_b, host_c, observed
  host_a = 2
  host_b = 3
  host_c = 40
  observed = -77
  call bare_case(observed)
  if (observed /= 6) error stop 1
  if (host_c /= 4) error stop 2
  host_c = 40
  call basic_case(observed)
  if (observed /= 45) error stop 3
  call only_case(observed)
  if (observed /= 12) error stop 4
  if (host_c /= 40) error stop 5
  call none_case(observed)
  if (observed /= 8) error stop 6
  if (host_c /= 40) error stop 7
  call all_case(observed)
  if (observed /= 11) error stop 8
  if (host_c /= 6) error stop 9
  write(*,'(a)') 'IMPORT STATEMENT C8104 SINGLE CONTROLS OK'
contains
  subroutine bare_case(out)
    import
    integer, intent(out) :: out
    host_c = 4
    out = host_a + host_c
  end subroutine
  subroutine basic_case(out)
    import host_a
    import :: host_b, host_c
    integer, intent(out) :: out
    out = host_a + host_b + host_c
  end subroutine
  subroutine only_case(out)
    import, only: host_a
    import, only: host_b
    integer, intent(out) :: out
    integer :: host_c
    host_c = 7
    out = host_a + host_b + host_c
  end subroutine
  subroutine none_case(out)
    import, none
    integer, intent(out) :: out
    integer :: host_c
    host_c = 8
    out = host_c
  end subroutine
  subroutine all_case(out)
    import, all
    integer, intent(out) :: out
    host_c = 6
    out = host_a + host_b + host_c
  end subroutine
end program import_statement_forms
