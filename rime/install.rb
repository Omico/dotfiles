require "./lib/core"

module RimeDeploy
  module CheckedConfigCommands
    def system(*args)
      checked = self.class.name.end_with?("::CloneConfigJob", "::CopyCustomConfigJob")
      super(*args, exception: checked)
    end
  end

  Job.prepend(CheckedConfigCommands)
end

load "./installer.rb"
