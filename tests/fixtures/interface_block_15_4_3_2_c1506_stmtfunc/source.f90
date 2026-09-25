program interface_block_c1506_stmtfunc_control
  implicit none
  interface
    subroutine s()
      integer :: f
      f() = 1
    end subroutine s
  end interface
  print '(a)', 'INTERFACE BLOCK C1506 STMTFUNC CONTROL OK'
end program interface_block_c1506_stmtfunc_control
