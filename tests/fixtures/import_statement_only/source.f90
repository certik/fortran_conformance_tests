program import_statement_only_effect
  implicit none
  integer :: hx, hy, hz, observed
  hx = 5
  hy = 6
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 18) error stop 1
  if (hz /= 100) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT ONLY OK'
contains
  subroutine inner(out)
    import, only: hx
    import, only: hy
    integer, intent(out) :: out
    integer :: hz
    hz = 7
    out = hx + hy + hz
  end subroutine
end program import_statement_only_effect
